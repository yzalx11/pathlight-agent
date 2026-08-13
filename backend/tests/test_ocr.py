import asyncio

import pytest
from fastapi import HTTPException

from app.services import ocr


class Upload:
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content


def test_rejects_non_image_upload():
    with pytest.raises(HTTPException) as error:
        asyncio.run(ocr.extract_job_screenshot(Upload("job.pdf", b"not an image")))
    assert error.value.status_code == 400
