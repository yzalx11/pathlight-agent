import re
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Job, JobScreenshot
from app.repositories import get_job
from app.schemas import JobPayload
from app.services.ocr import IMAGE_SUFFIXES, extract_text_from_path
from app.services.trace import record_trace


def _first_match(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""


def infer_job_metadata(text: str) -> dict[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = ""
    for line in lines[:12]:
        if (
            2 <= len(line) <= 48
            and not re.search(r"\d{1,3}[Kk]", line)
            and not any(marker in line for marker in ("职位描述", "任职要求", "岗位职责", "立即沟通"))
        ):
            title = line
            break
    return {
        "title": title,
        "salary": _first_match(r"((?:\d{1,3}(?:\.\d+)?\s*[-~]\s*\d{1,3}(?:\.\d+)?|\d{1,3})\s*[Kk](?:\s*[·.]?\s*\d{1,2}\s*薪)?)", text),
        "city": _first_match(r"(北京|上海|广州|深圳|杭州|东莞|成都|武汉|西安|南京|苏州|长沙|重庆|天津|厦门|宁波)", text),
        "experience": _first_match(r"((?:\d+\s*[-~]\s*\d+|\d+)\s*年|经验不限)", text),
        "education": _first_match(r"(本科|硕士|博士|大专|学历不限)", text),
    }


async def create_job_from_screenshots(db: Session, files: list[UploadFile]) -> Job:
    if not files:
        raise HTTPException(status_code=422, detail="Select at least one job screenshot.")
    if len(files) > 8:
        raise HTTPException(status_code=422, detail="Upload no more than 8 screenshots at a time.")

    job_dir = settings.upload_dir / "jobs"
    job_dir.mkdir(parents=True, exist_ok=True)
    image_records: list[dict[str, str]] = []
    try:
        for file in files:
            suffix = Path(file.filename or "").suffix.lower()
            if suffix not in IMAGE_SUFFIXES:
                raise HTTPException(status_code=400, detail="Only job screenshot image files are supported.")
            content = await file.read()
            if not content:
                raise HTTPException(status_code=422, detail="One uploaded screenshot is empty.")
            if len(content) > settings.max_upload_size_bytes:
                raise HTTPException(status_code=413, detail="Screenshot exceeds the 10 MB upload limit.")
            storage_path = job_dir / f"{uuid4().hex}{suffix}"
            storage_path.write_bytes(content)
            image_records.append(
                {
                    "filename": file.filename or storage_path.name,
                    "storage_path": str(storage_path),
                    "ocr_text": extract_text_from_path(storage_path),
                }
            )
    except Exception:
        for record in image_records:
            Path(record["storage_path"]).unlink(missing_ok=True)
        raise

    ocr_text = "\n\n".join(record["ocr_text"] for record in image_records)
    metadata = infer_job_metadata(ocr_text)
    job = Job(
        **metadata,
        source="boss_screenshot",
        ocr_text=ocr_text,
        jd_text=ocr_text,
    )
    db.add(job)
    db.flush()
    db.add_all(JobScreenshot(job_id=job.id, **record) for record in image_records)
    record_trace(db, "import_job_screenshots", f"Imported {len(image_records)} BOSS job screenshots.")
    db.commit()
    db.refresh(job)
    return get_job(db, job.id) or job


def update_job(db: Session, job_id: int, payload: JobPayload) -> Job:
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    for field, value in payload.model_dump(mode="json").items():
        setattr(job, field, value)
    record_trace(db, "update_job", f"Updated job draft #{job.id}.")
    db.commit()
    return get_job(db, job_id) or job
