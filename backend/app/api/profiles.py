from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.repositories import get_preference, list_resumes
from app.schemas import FactUpdate, JdPayload, MatchPayload, MatchRead, PreferencePayload, ResumeRead, SavedResponse
from app.services.jd import parse_jd
from app.services.matching import analyze_match
from app.services.profile import create_resume, save_preferences, update_fact
from app.database import get_db

router = APIRouter()


@router.get("/resumes", response_model=list[ResumeRead])
def get_resumes(db: Session = Depends(get_db)) -> list[ResumeRead]:
    return list_resumes(db)


@router.post("/resumes", response_model=ResumeRead, status_code=201)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)) -> ResumeRead:
    return await create_resume(db, file)


@router.put("/facts/{fact_id}", response_model=SavedResponse)
def save_fact(fact_id: int, payload: FactUpdate, db: Session = Depends(get_db)) -> SavedResponse:
    update_fact(db, fact_id, payload)
    return SavedResponse()


@router.get("/preferences", response_model=PreferencePayload)
def get_preferences(db: Session = Depends(get_db)) -> PreferencePayload:
    preference = get_preference(db)
    return PreferencePayload.model_validate(preference, from_attributes=True) if preference else PreferencePayload()


@router.put("/preferences", response_model=SavedResponse)
def put_preferences(payload: PreferencePayload, db: Session = Depends(get_db)) -> SavedResponse:
    save_preferences(db, payload)
    return SavedResponse()


@router.post("/jd/parse")
def parse_job_description(payload: JdPayload) -> dict:
    return parse_jd(payload.jd_text)


@router.post("/matches", response_model=MatchRead)
def create_match(payload: MatchPayload, db: Session = Depends(get_db)) -> MatchRead:
    return analyze_match(db, payload)
