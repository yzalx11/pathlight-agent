from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Fact, Preference, Resume
from app.repositories import get_preference
from app.schemas import FactUpdate, PreferencePayload
from app.services.document_parser import build_candidate_facts, extract_text
from app.services.trace import record_trace


async def create_resume(db: Session, file: UploadFile) -> Resume:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX resumes are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="The uploaded resume is empty.")
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="Resume exceeds the 10 MB upload limit.")

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    storage_path = settings.upload_dir / f"{uuid4().hex}{suffix}"
    storage_path.write_bytes(content)
    try:
        text = extract_text(storage_path)
        facts = build_candidate_facts(text)
    except Exception as exc:
        storage_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not facts:
        storage_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="No readable resume facts were found.")

    resume = Resume(filename=file.filename or storage_path.name, storage_path=str(storage_path))
    db.add(resume)
    db.flush()
    db.add_all(Fact(resume_id=resume.id, **fact_data) for fact_data in facts)
    record_trace(db, "parse_resume", f"Parsed {resume.filename} into {len(facts)} candidate facts.")
    db.commit()
    db.refresh(resume)
    return resume


def update_fact(db: Session, fact_id: int, payload: FactUpdate) -> None:
    fact = db.get(Fact, fact_id)
    if fact is None:
        raise HTTPException(status_code=404, detail="Fact not found.")
    fact.category = payload.category.value
    fact.content = payload.content
    fact.status = payload.status.value
    record_trace(db, "confirm_facts", f"{fact.fact_code} marked {fact.status}.")
    db.commit()


def save_preferences(db: Session, payload: PreferencePayload) -> None:
    preference = get_preference(db)
    values = payload.model_dump()
    if preference is None:
        db.add(Preference(**values))
    else:
        for field, value in values.items():
            setattr(preference, field, value)
    record_trace(db, "save_preferences", "Updated job-search preferences.")
    db.commit()
