from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, init_db
from app.models import Application, Fact, Preference, Resume, TraceRun
from app.schemas import (
    ApiKeyPayload,
    ApplicationPayload,
    ApplicationRead,
    FactUpdate,
    JdPayload,
    MatchPayload,
    PreferencePayload,
    ResumeRead,
)
from app.services.credentials import has_deepseek_key, save_deepseek_key
from app.services.document_parser import build_candidate_facts, extract_text
from app.services.jd import draft_greeting, fact_check_draft, match_resume_to_jd, parse_jd


app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    init_db()


@app.get("/health")
def health() -> dict:
    return {"ok": True, "has_deepseek_key": has_deepseek_key()}


@app.post("/settings/deepseek-key")
def set_deepseek_key(payload: ApiKeyPayload) -> dict:
    save_deepseek_key(payload.api_key)
    return {"saved": True}


@app.post("/resumes", response_model=ResumeRead)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)) -> Resume:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX resumes are supported.")

    storage_name = f"{uuid4().hex}{suffix}"
    storage_path = settings.upload_dir / storage_name
    storage_path.write_bytes(await file.read())

    try:
        text = extract_text(storage_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    resume = Resume(filename=file.filename or storage_name, storage_path=str(storage_path))
    db.add(resume)
    db.flush()

    for fact_data in build_candidate_facts(text):
        db.add(Fact(resume_id=resume.id, **fact_data))

    _trace(db, "parse_resume", "completed", f"Parsed resume {resume.filename}")
    db.commit()
    db.refresh(resume)
    return resume


@app.get("/resumes", response_model=list[ResumeRead])
def list_resumes(db: Session = Depends(get_db)) -> list[Resume]:
    return db.query(Resume).order_by(Resume.created_at.desc()).all()


@app.put("/facts/{fact_id}")
def update_fact(fact_id: int, payload: FactUpdate, db: Session = Depends(get_db)) -> dict:
    fact = db.get(Fact, fact_id)
    if fact is None:
        raise HTTPException(status_code=404, detail="Fact not found.")

    if payload.status not in {"candidate", "confirmed", "rejected"}:
        raise HTTPException(status_code=400, detail="Fact status must be candidate, confirmed, or rejected.")

    fact.category = payload.category or fact.category
    fact.content = payload.content
    fact.status = payload.status
    _trace(db, "confirm_facts", "completed", f"{fact.fact_code}: {fact.status}")
    db.commit()
    return {"saved": True}


@app.post("/preferences")
def save_preferences(payload: PreferencePayload, db: Session = Depends(get_db)) -> dict:
    preference = db.query(Preference).first()
    if preference is None:
        preference = Preference(**payload.model_dump())
        db.add(preference)
    else:
        for key, value in payload.model_dump().items():
            setattr(preference, key, value)
    db.commit()
    return {"saved": True}


@app.get("/preferences")
def get_preferences(db: Session = Depends(get_db)) -> dict:
    preference = db.query(Preference).first()
    return PreferencePayload.model_validate(preference, from_attributes=True).model_dump() if preference else {}


@app.post("/jd/parse")
def parse_job_description(payload: JdPayload) -> dict:
    return parse_jd(payload.jd_text)


@app.post("/match")
def match(payload: MatchPayload, db: Session = Depends(get_db)) -> dict:
    facts = db.query(Fact).filter(Fact.resume_id == payload.resume_id, Fact.status != "rejected").all()
    if not facts:
        raise HTTPException(status_code=404, detail="Resume facts not found.")
    result = match_resume_to_jd(facts, payload.jd_text)
    result["greeting"] = draft_greeting(result)
    result["fact_check"] = fact_check_draft(result["greeting"], {fact.fact_code for fact in facts})
    _trace(db, "match_profile_to_jd", "completed", result["recommendation"])
    db.commit()
    return result


@app.post("/applications", response_model=ApplicationRead)
def create_application(payload: ApplicationPayload, db: Session = Depends(get_db)) -> Application:
    application = Application(**payload.model_dump())
    db.add(application)
    _trace(db, "save_application", "completed", f"{payload.company} - {payload.position}")
    db.commit()
    db.refresh(application)
    return application


@app.get("/applications", response_model=list[ApplicationRead])
def list_applications(db: Session = Depends(get_db)) -> list[Application]:
    return db.query(Application).order_by(Application.created_at.desc()).all()


@app.get("/trace")
def list_trace(db: Session = Depends(get_db)) -> list[dict]:
    runs = db.query(TraceRun).order_by(TraceRun.created_at.desc()).limit(50).all()
    return [
        {
            "run_id": run.run_id,
            "task_type": run.task_type,
            "status": run.status,
            "summary": run.summary,
            "created_at": run.created_at,
        }
        for run in runs
    ]


def _trace(db: Session, task_type: str, status: str, summary: str) -> None:
    db.add(TraceRun(run_id=uuid4().hex[:12], task_type=task_type, status=status, summary=summary))
