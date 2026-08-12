from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import TraceRun
from app.schemas import TraceStatus


def record_trace(db: Session, task_type: str, summary: str, status: TraceStatus = TraceStatus.COMPLETED) -> None:
    db.add(
        TraceRun(
            run_id=uuid4().hex[:12],
            task_type=task_type,
            status=status.value,
            summary=summary[:2_000],
        )
    )
