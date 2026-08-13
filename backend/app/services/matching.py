from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.llm.deepseek import generate_job_insight
from app.llm.validators import validate_job_insight
from app.repositories import get_preference, get_resume
from app.schemas import MatchPayload
from app.services.jd import draft_greeting, fact_check_draft, match_resume_to_jd
from app.services.trace import record_trace


def analyze_match(db: Session, payload: MatchPayload) -> dict:
    resume = get_resume(db, payload.resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found.")

    facts = [fact for fact in resume.facts if fact.status != "rejected"]
    confirmed_facts = [fact for fact in facts if fact.status == "confirmed"]
    usable_facts = confirmed_facts or facts
    if not usable_facts:
        raise HTTPException(status_code=422, detail="Confirm at least one resume fact before analysis.")

    preference = get_preference(db)
    result = match_resume_to_jd(usable_facts, payload.jd_text, preference)
    result["greeting"] = draft_greeting(result)
    result["fact_check"] = fact_check_draft(
        result["greeting"], {fact.fact_code for fact in usable_facts}
    )
    confirmed_facts = [fact for fact in usable_facts if fact.status == "confirmed"]
    insight = generate_job_insight(
        payload.jd_text,
        [
            {"fact_code": fact.fact_code, "content": fact.content}
            for fact in confirmed_facts
        ],
    )
    if insight is not None:
        result["llm_insight"] = validate_job_insight(
            insight, {fact.fact_code for fact in confirmed_facts}
        )
    record_trace(db, "match_profile_to_jd", result["recommendation"])
    db.commit()
    return result
