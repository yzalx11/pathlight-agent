from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Job
from app.repositories import get_job
from app.schemas import BrowserJobImportPayload, BrowserJobPreviewPayload
from app.services.jobs import infer_job_metadata
from app.services.trace import record_trace


def _is_supported_job_url(source_link: str) -> bool:
    hostname = (urlparse(source_link).hostname or "").lower()
    return hostname == "zhipin.com" or hostname.endswith(".zhipin.com")


def _normalized_text(visible_text: str) -> str:
    return "\n".join(line.strip() for line in visible_text.splitlines() if line.strip())


def build_browser_job_preview(payload: BrowserJobPreviewPayload) -> dict[str, str]:
    if not _is_supported_job_url(payload.source_link):
        raise HTTPException(
            status_code=422,
            detail="This bridge currently supports a visible BOSS job page only.",
        )

    visible_text = _normalized_text(payload.visible_text)
    metadata = infer_job_metadata(visible_text)
    title = metadata["title"] or payload.page_title
    return {
        **metadata,
        "title": title[:255],
        "company": "",
        "source_link": payload.source_link,
        "jd_excerpt": visible_text[:800],
    }


def create_browser_job_draft(db: Session, payload: BrowserJobImportPayload) -> Job:
    preview = build_browser_job_preview(payload)
    visible_text = _normalized_text(payload.visible_text)
    values = {
        field: getattr(payload, field) or preview[field]
        for field in ("company", "title", "city", "salary", "experience", "education")
    }
    job = Job(
        **values,
        source="browser_bridge",
        source_link=payload.source_link,
        ocr_text=visible_text,
        jd_text=visible_text,
    )
    db.add(job)
    db.flush()
    record_trace(db, "import_browser_job", f"Imported visible BOSS job page into draft #{job.id}.")
    db.commit()
    return get_job(db, job.id) or job
