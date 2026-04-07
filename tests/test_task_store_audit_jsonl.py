from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.config import settings
from app.models import TaskRecord
from app.task_store import append_jsonl_audit


def test_append_jsonl_audit_writes_one_json_line(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = tmp_path / "events.jsonl"
    monkeypatch.setattr(settings, "task_jsonl_path", str(p))

    row = TaskRecord(
        id="t1",
        created_at=datetime.now(timezone.utc),
        status="completed",
        user_message="hi",
        final_answer="ok",
        trace_json=json.dumps([{"type": "usage", "total_tokens": 3}]),
        latency_ms=1.23,
        prompt_tokens=1,
        completion_tokens=2,
        total_tokens=3,
        error_message=None,
    )

    append_jsonl_audit(row)

    text = p.read_text(encoding="utf-8").strip()
    payload = json.loads(text)
    assert payload["task_id"] == "t1"
    assert payload["status"] == "completed"
    assert payload["final_answer"] == "ok"
    assert isinstance(payload["trace"], list)


def test_append_jsonl_audit_noop_when_disabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = tmp_path / "events.jsonl"
    monkeypatch.setattr(settings, "task_jsonl_path", "")

    row = TaskRecord(
        id="t2",
        created_at=datetime.now(timezone.utc),
        status="completed",
        user_message="hi",
        final_answer="ok",
        trace_json="[]",
        latency_ms=None,
        prompt_tokens=None,
        completion_tokens=None,
        total_tokens=None,
        error_message=None,
    )
    append_jsonl_audit(row)
    assert not p.exists()

