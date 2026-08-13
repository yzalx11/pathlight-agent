from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import dashboard_counts, list_action_jobs, list_trace
from app.schemas import ActionItemRead, DashboardRead, JobStatus, TraceRead

router = APIRouter()


@router.get("/dashboard", response_model=DashboardRead)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardRead:
    resumes_total, facts_confirmed, applications_total, follow_up_total = dashboard_counts(db)
    action_labels = {
        JobStatus.PENDING_REVIEW.value: "校对职位信息",
        JobStatus.READY.value: "决定是否发起沟通",
        JobStatus.CONTACTED.value: "继续沟通",
        JobStatus.WAITING.value: "检查是否需要跟进",
        JobStatus.READ_NO_REPLY.value: "判断是否补充跟进",
        JobStatus.ASSESSMENT.value: "准备笔试或作业",
        JobStatus.INTERVIEW.value: "准备面试",
    }
    return DashboardRead(
        resumes_total=resumes_total,
        facts_confirmed=facts_confirmed,
        applications_total=applications_total,
        follow_up_total=follow_up_total,
        action_items=[
            ActionItemRead(
                job_id=job.id,
                title=job.title or "未命名职位",
                company=job.company or "待确认公司",
                status=JobStatus(job.status),
                action=action_labels[job.status],
                next_action_at=job.next_action_at,
            )
            for job in list_action_jobs(db)
        ],
        recent_trace=[TraceRead.model_validate(item, from_attributes=True) for item in list_trace(db)],
    )
