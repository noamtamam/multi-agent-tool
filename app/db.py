import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import Base

# Ensure directory exists for SQLite file path
if settings.database_url.startswith("sqlite:///./"):
    path = settings.database_url.replace("sqlite:///./", "", 1)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
