from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import list_jobs
from app.schemas import JobPayload, JobRead
from app.services.jobs import create_job_from_screenshots, update_job

router = APIRouter()


@router.get("/jobs", response_model=list[JobRead])
def get_jobs(db: Session = Depends(get_db)) -> list[JobRead]:
    return list_jobs(db)


@router.post("/jobs/import-screenshots", response_model=JobRead, status_code=201)
async def import_job_screenshots(
    files: list[UploadFile] = File(...), db: Session = Depends(get_db)
) -> JobRead:
    return await create_job_from_screenshots(db, files)


@router.put("/jobs/{job_id}", response_model=JobRead)
def put_job(job_id: int, payload: JobPayload, db: Session = Depends(get_db)) -> JobRead:
    return update_job(db, job_id, payload)
