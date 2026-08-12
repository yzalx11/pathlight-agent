from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import dashboard_counts, list_trace
from app.schemas import DashboardRead, TraceRead

router = APIRouter()


@router.get("/dashboard", response_model=DashboardRead)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardRead:
    resumes_total, facts_confirmed, applications_total, follow_up_total = dashboard_counts(db)
    return DashboardRead(
        resumes_total=resumes_total,
        facts_confirmed=facts_confirmed,
        applications_total=applications_total,
        follow_up_total=follow_up_total,
        recent_trace=[TraceRead.model_validate(item, from_attributes=True) for item in list_trace(db)],
    )
