from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Application
from app.repositories import list_applications
from app.schemas import ApplicationPayload, ApplicationRead
from app.services.trace import record_trace

router = APIRouter()


@router.get("/applications", response_model=list[ApplicationRead])
def get_applications(db: Session = Depends(get_db)) -> list[ApplicationRead]:
    return list_applications(db)


@router.post("/applications", response_model=ApplicationRead, status_code=201)
def create_application(payload: ApplicationPayload, db: Session = Depends(get_db)) -> ApplicationRead:
    application = Application(**payload.model_dump(mode="json"))
    db.add(application)
    record_trace(db, "save_application", f"Saved {payload.company} / {payload.position} as {payload.status.value}.")
    db.commit()
    db.refresh(application)
    return application
