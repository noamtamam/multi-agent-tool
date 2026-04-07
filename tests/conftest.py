"""Test fixtures: isolated SQLite DB for API tests via patched app.db engine."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base


@pytest.fixture
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator:
    url = f"sqlite:///{(tmp_path / 'api_test.db').as_posix()}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    import app.db as db

    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", session_local)

    import app.task_store as ts

    monkeypatch.setattr(ts, "append_jsonl_audit", lambda row: None)

    from app.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        yield client
