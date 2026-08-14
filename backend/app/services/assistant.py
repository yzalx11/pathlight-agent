from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.llm.deepseek import generate_reply_drafts
from app.llm.validators import validate_reply_drafts
from app.repositories import get_job, get_resume
from app.schemas import ReplyDraftPayload
from app.services.trace import record_trace


def _job_context(job) -> str:
    details = [
        f"Company: {job.company or 'Unknown'}",
        f"Role: {job.title or 'Unknown'}",
        f"City: {job.city or 'Not specified'}",
    ]
    if job.jd_text:
        details.append(f"Job description:\n{job.jd_text}")
    if job.notes:
        details.append(f"User notes:\n{job.notes}")
    return "\n".join(details)


def create_reply_drafts(db: Session, payload: ReplyDraftPayload) -> dict:
    resume = get_resume(db, payload.resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found.")

    job = get_job(db, payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    facts = [fact for fact in resume.facts if fact.status == "confirmed"]
    if not facts:
        raise HTTPException(
            status_code=422,
            detail="Confirm at least one resume fact before drafting a reply.",
        )

    draft_set = generate_reply_drafts(
        question=payload.question,
        job_context=_job_context(job),
        facts=[{"fact_code": fact.fact_code, "content": fact.content} for fact in facts],
    )
    if draft_set is None:
        raise HTTPException(
            status_code=503,
            detail="The local model connection is unavailable. Check your API key and try again.",
        )

    validated = validate_reply_drafts(draft_set, {fact.fact_code for fact in facts})
    if validated is None:
        raise HTTPException(
            status_code=502,
            detail="The model returned drafts without usable confirmed facts. Try a more specific question.",
        )

    result = validated.model_dump()
    record_trace(db, "draft_recruiter_reply", f"Generated {len(result['drafts'])} reply drafts.")
    db.commit()
    return result
