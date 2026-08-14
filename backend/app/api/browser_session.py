from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import list_browser_imports
from app.schemas import BrowserImportRead, BrowserScanRead, BrowserSessionRead, JobRead, SavedResponse
from app.services.browser_imports import (
    confirm_browser_import,
    dismiss_browser_import,
    scan_visible_browser_job,
)
from app.services.browser_session import browser_session_status, launch_recruiting_browser


router = APIRouter(prefix="/browser")


@router.get("/session", response_model=BrowserSessionRead)
def get_browser_session() -> BrowserSessionRead:
    return browser_session_status()


@router.post("/session/launch", response_model=BrowserSessionRead)
def launch_browser_session() -> BrowserSessionRead:
    return launch_recruiting_browser()


@router.post("/session/scan", response_model=BrowserScanRead)
def scan_browser_session(db: Session = Depends(get_db)) -> BrowserScanRead:
    status, browser_import = scan_visible_browser_job(db)
    messages = {
        "captured": "Captured the visible job page for review.",
        "existing": "This visible job page is already in the local queue.",
        "no_active_job": "No visible BOSS job detail page is active.",
    }
    return BrowserScanRead(
        status=status,
        import_id=browser_import.id if browser_import else None,
        message=messages[status],
    )


@router.get("/imports", response_model=list[BrowserImportRead])
def get_browser_imports(db: Session = Depends(get_db)) -> list[BrowserImportRead]:
    return [BrowserImportRead.model_validate(item, from_attributes=True) for item in list_browser_imports(db)]


@router.post("/imports/{import_id}/confirm", response_model=JobRead)
def confirm_import(import_id: int, db: Session = Depends(get_db)) -> JobRead:
    return confirm_browser_import(db, import_id)


@router.post("/imports/{import_id}/dismiss", response_model=SavedResponse)
def dismiss_import(import_id: int, db: Session = Depends(get_db)) -> SavedResponse:
    dismiss_browser_import(db, import_id)
    return SavedResponse()
