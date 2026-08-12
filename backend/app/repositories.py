from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Application, Fact, Preference, Resume, TraceRun
from app.schemas import FactStatus


def list_resumes(db: Session) -> Sequence[Resume]:
    statement = select(Resume).options(selectinload(Resume.facts)).order_by(Resume.created_at.desc())
    return db.scalars(statement).all()


def get_resume(db: Session, resume_id: int) -> Resume | None:
    statement = select(Resume).options(selectinload(Resume.facts)).where(Resume.id == resume_id)
    return db.scalar(statement)


def get_preference(db: Session) -> Preference | None:
    return db.scalar(select(Preference).limit(1))


def list_applications(db: Session) -> Sequence[Application]:
    return db.scalars(select(Application).order_by(Application.created_at.desc())).all()


def list_trace(db: Session, limit: int = 12) -> Sequence[TraceRun]:
    return db.scalars(select(TraceRun).order_by(TraceRun.created_at.desc()).limit(limit)).all()


def dashboard_counts(db: Session) -> tuple[int, int, int, int]:
    resumes_total = db.scalar(select(func.count()).select_from(Resume)) or 0
    facts_confirmed = db.scalar(
        select(func.count()).select_from(Fact).where(Fact.status == FactStatus.CONFIRMED.value)
    ) or 0
    applications_total = db.scalar(select(func.count()).select_from(Application)) or 0
    follow_up_total = db.scalar(
        select(func.count()).select_from(Application).where(Application.status == "follow_up")
    ) or 0
    return resumes_total, facts_confirmed, applications_total, follow_up_total
