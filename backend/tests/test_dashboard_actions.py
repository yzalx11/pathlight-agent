from datetime import datetime

from app.api.dashboard import get_dashboard
from app.database import SessionLocal, init_db
from app.models import Job


def test_dashboard_includes_read_no_reply_job_as_action_item():
    init_db()
    db = SessionLocal()
    try:
        job = Job(
            title="AI Agent 开发工程师",
            company="示例公司",
            status="read_no_reply",
            next_action_at=datetime(2026, 8, 20, 9),
            jd_text="需要校对的岗位信息",
        )
        db.add(job)
        db.commit()

        dashboard = get_dashboard(db)
        action = next(item for item in dashboard.action_items if item.job_id == job.id)
        assert action.status.value == "read_no_reply"
        assert action.action == "判断是否补充跟进"
    finally:
        db.rollback()
        if job.id is not None:
            db.delete(job)
            db.commit()
        db.close()
