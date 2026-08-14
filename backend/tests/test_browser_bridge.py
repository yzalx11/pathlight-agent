import pytest
from fastapi import HTTPException

from app.schemas import BrowserJobPreviewPayload
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
