import hashlib

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import BrowserImport, Job
from app.repositories import get_browser_import
from app.services.browser_bridge import build_browser_job_preview
from app.services.browser_session import capture_visible_boss_job
from app.services.trace import record_trace


def scan_visible_browser_job(db: Session) -> tuple[str, BrowserImport | None]:
    payload = capture_visible_boss_job()
    if payload is None:
        return "no_active_job", None

    fingerprint = hashlib.sha256(
        f"{payload.source_link}\n{payload.visible_text}".encode("utf-8")
    ).hexdigest()
    existing = db.scalar(select(BrowserImport).where(BrowserImport.fingerprint == fingerprint))
    if existing is not None:
        return "existing", existing

    preview = build_browser_job_preview(payload)
    browser_import = BrowserImport(
        fingerprint=fingerprint,
        page_title=payload.page_title,
        source_link=payload.source_link,
        visible_text=payload.visible_text,
        company=preview["company"],
        title=preview["title"],
        city=preview["city"],
        salary=preview["salary"],
        experience=preview["experience"],
        education=preview["education"],
    )
    db.add(browser_import)
    record_trace(db, "capture_browser_job", "Captured a visible BOSS job page for review.")
    db.commit()
    db.refresh(browser_import)
    return "captured", browser_import


def confirm_browser_import(db: Session, import_id: int) -> Job:
    browser_import = get_browser_import(db, import_id)
    if browser_import is None:
        raise HTTPException(status_code=404, detail="Browser import not found.")
    if browser_import.status != "pending":
        raise HTTPException(status_code=409, detail="Browser import has already been handled.")

    job = Job(
        company=browser_import.company,
        title=browser_import.title,
        city=browser_import.city,
        salary=browser_import.salary,
        experience=browser_import.experience,
        education=browser_import.education,
        source="browser_cdp",
        source_link=browser_import.source_link,
        ocr_text=browser_import.visible_text,
        jd_text=browser_import.visible_text,
    )
    browser_import.status = "confirmed"
    db.add(job)
    db.flush()
    record_trace(db, "confirm_browser_job", f"Confirmed browser import #{browser_import.id} as job #{job.id}.")
    db.commit()
    db.refresh(job)
    return job


def dismiss_browser_import(db: Session, import_id: int) -> None:
    browser_import = get_browser_import(db, import_id)
    if browser_import is None:
        raise HTTPException(status_code=404, detail="Browser import not found.")
    if browser_import.status != "pending":
        raise HTTPException(status_code=409, detail="Browser import has already been handled.")
    browser_import.status = "dismissed"
    record_trace(db, "dismiss_browser_job", f"Dismissed browser import #{browser_import.id}.")
    db.commit()
