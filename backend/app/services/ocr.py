from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from rapidocr import RapidOCR

from app.config import settings


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
_ocr: RapidOCR | None = None


def _get_ocr() -> RapidOCR:
    global _ocr
    if _ocr is None:
        _ocr = RapidOCR()
    return _ocr


async def extract_job_screenshot(file: UploadFile) -> dict[str, int | str]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in IMAGE_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail="Only PNG, JPG, JPEG, and WebP job screenshots are supported.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="The uploaded screenshot is empty.")
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="Screenshot exceeds the 10 MB upload limit.")

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = settings.upload_dir / f"ocr-{uuid4().hex}{suffix}"
    temp_path.write_bytes(content)
    try:
        result = _get_ocr()(str(temp_path))
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Unable to read text from screenshot.") from exc
    finally:
        temp_path.unlink(missing_ok=True)

    lines = [str(text).strip() for text in (result.txts if result else ()) if str(text).strip()]
    text = "\n".join(lines)
    if len(text) < 10:
        raise HTTPException(
            status_code=422,
            detail="Too little readable text was found. Please use a clearer screenshot.",
        )
    return {"text": text, "lines_detected": len(lines)}
