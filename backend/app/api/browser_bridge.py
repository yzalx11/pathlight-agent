from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    BrowserJobImportPayload,
    BrowserJobPreviewPayload,
    BrowserJobPreviewRead,
    JobRead,
)
from app.services.browser_bridge import build_browser_job_preview, create_browser_job_draft


router = APIRouter(prefix="/bridge")


@router.post("/job-preview", response_model=BrowserJobPreviewRead)
def preview_browser_job(payload: BrowserJobPreviewPayload) -> BrowserJobPreviewRead:
    return BrowserJobPreviewRead(**build_browser_job_preview(payload))


@router.post("/jobs", response_model=JobRead, status_code=201)
def import_browser_job(
    payload: BrowserJobImportPayload, db: Session = Depends(get_db)
) -> JobRead:
    return create_browser_job_draft(db, payload)
