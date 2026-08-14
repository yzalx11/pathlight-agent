import pytest
from fastapi import HTTPException

from app.schemas import BrowserJobPreviewPayload
from app.database import SessionLocal, init_db
from app.models import BrowserImport, Job
from app.services import browser_imports
from app.services.browser_bridge import build_browser_job_preview


def test_browser_preview_uses_visible_boss_job_text() -> None:
    preview = build_browser_job_preview(
        BrowserJobPreviewPayload(
            page_title="Python 后端开发工程师 - 测试公司",
            source_link="https://www.zhipin.com/job_detail/example.html",
            visible_text="""Python 后端开发工程师
测试公司
上海 15-25K
岗位职责
负责 FastAPI 服务开发和数据接口维护
任职要求
3年经验 本科""",
        )
    )

    assert preview["title"] == "Python 后端开发工程师"
    assert preview["city"] == "上海"
    assert preview["salary"] == "15-25K"
    assert "岗位职责" in preview["jd_excerpt"]


def test_browser_preview_rejects_other_platforms_for_first_release() -> None:
    payload = BrowserJobPreviewPayload(
        page_title="Example role",
        source_link="https://example.com/jobs/1",
        visible_text="A visible job description with enough content for validation.",
    )

    with pytest.raises(HTTPException, match="BOSS"):
        build_browser_job_preview(payload)


def test_browser_capture_enters_queue_then_requires_confirmation(monkeypatch) -> None:
    payload = BrowserJobPreviewPayload(
        page_title="AI Agent 开发工程师 - 示例公司",
        source_link="https://www.zhipin.com/web/geek/job?jobId=example",
        visible_text="""AI Agent 开发工程师
示例公司
杭州 10-15K
职位描述
参与 AI Agent 应用开发。
任职要求
1-3年 本科""",
    )
    monkeypatch.setattr(browser_imports, "capture_visible_boss_job", lambda: payload)
    init_db()
    db = SessionLocal()
    browser_import = None
    job = None
    try:
        status, browser_import = browser_imports.scan_visible_browser_job(db)
        assert status == "captured"
        assert browser_import is not None
        assert browser_import.status == "pending"

        duplicate_status, duplicate = browser_imports.scan_visible_browser_job(db)
        assert duplicate_status == "existing"
        assert duplicate.id == browser_import.id

        job = browser_imports.confirm_browser_import(db, browser_import.id)
        assert job.source == "browser_cdp"
        assert browser_import.status == "confirmed"
    finally:
        if job is not None:
            db.delete(job)
        if browser_import is not None:
            stored_import = db.get(BrowserImport, browser_import.id)
            if stored_import is not None:
                db.delete(stored_import)
        db.commit()
        db.close()
