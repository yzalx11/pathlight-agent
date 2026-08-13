from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Application, Fact, Job, Preference, Resume, TraceRun
from app.schemas import FactStatus, JobStatus


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


def list_jobs(db: Session) -> Sequence[Job]:
    statement = select(Job).options(selectinload(Job.screenshots)).order_by(Job.created_at.desc())
    return db.scalars(statement).all()


def get_job(db: Session, job_id: int) -> Job | None:
    statement = select(Job).options(selectinload(Job.screenshots)).where(Job.id == job_id)
    return db.scalar(statement)


def list_trace(db: Session, limit: int = 12) -> Sequence[TraceRun]:
    return db.scalars(select(TraceRun).order_by(TraceRun.created_at.desc()).limit(limit)).all()


def list_action_jobs(db: Session, limit: int = 6) -> Sequence[Job]:
    active_statuses = (
        JobStatus.PENDING_REVIEW.value,
        JobStatus.READY.value,
        JobStatus.CONTACTED.value,
        JobStatus.WAITING.value,
        JobStatus.READ_NO_REPLY.value,
        JobStatus.ASSESSMENT.value,
        JobStatus.INTERVIEW.value,
    )
    statement = (
        select(Job)
        .where(Job.status.in_(active_statuses))
        .order_by(Job.next_action_at.is_(None), Job.next_action_at.asc(), Job.updated_at.desc())
        .limit(limit)
    )
    return db.scalars(statement).all()


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
