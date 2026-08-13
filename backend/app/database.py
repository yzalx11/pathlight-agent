from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith("sqlite"):
        _migrate_sqlite()


def _migrate_sqlite() -> None:
    """Keep early local databases compatible while the desktop schema evolves."""
    with engine.begin() as connection:
        columns = {
            row[1] for row in connection.execute(text("PRAGMA table_info(jobs)")).fetchall()
        }
        if "next_action_at" not in columns:
            connection.execute(text("ALTER TABLE jobs ADD COLUMN next_action_at DATETIME"))
        if "notes" not in columns:
            connection.execute(text("ALTER TABLE jobs ADD COLUMN notes TEXT NOT NULL DEFAULT ''"))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
