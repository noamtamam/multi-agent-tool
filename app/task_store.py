"""Persist task runs to the database and optional JSONL audit file."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models import TaskRecord
from app.schemas import TaskStoredResponse

logger = logging.getLogger(__name__)


def row_to_stored_response(row: TaskRecord) -> TaskStoredResponse:
    trace: list[dict[str, Any]]
    try:
        trace = json.loads(row.trace_json) if row.trace_json else []
    except json.JSONDecodeError:
        trace = []
    return TaskStoredResponse(
        task_id=row.id,
        created_at=row.created_at,
        status=row.status,
        user_message=row.user_message,
        final_answer=row.final_answer,
        trace=trace,
        latency_ms=row.latency_ms,
        prompt_tokens=row.prompt_tokens,
        completion_tokens=row.completion_tokens,
        total_tokens=row.total_tokens,
        error=row.error_message,
    )


def _audit_payload(row: TaskRecord) -> dict[str, Any]:
    return {
        "task_id": row.id,
        "created_at": row.created_at.isoformat(),
        "status": row.status,
        "user_message": row.user_message,
        "final_answer": row.final_answer,
        "trace": json.loads(row.trace_json) if row.trace_json else [],
        "latency_ms": row.latency_ms,
        "prompt_tokens": row.prompt_tokens,
        "completion_tokens": row.completion_tokens,
        "total_tokens": row.total_tokens,
        "error": row.error_message,
    }


def append_jsonl_audit(row: TaskRecord) -> None:
    path = (settings.task_jsonl_path or "").strip()
    if not path:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(_audit_payload(row), default=str)
    with p.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def log_task_metrics(
    *,
    task_id: str,
    status: str,
    latency_ms: float | None,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    total_tokens: int | None,
) -> None:
    logger.info(
        "task_metrics task_id=%s status=%s latency_ms=%s prompt_tokens=%s "
        "completion_tokens=%s total_tokens=%s",
        task_id,
        status,
        f"{latency_ms:.2f}" if latency_ms is not None else "null",
        prompt_tokens,
        completion_tokens,
        total_tokens,
    )


def save_task_record(
    session: Session,
    *,
    task_id: str,
    user_message: str,
    status: str,
    final_answer: str | None,
    trace: list[dict[str, Any]],
    latency_ms: float | None,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    total_tokens: int | None,
    error_message: str | None = None,
) -> TaskRecord:
    now = datetime.now(timezone.utc)
    row = TaskRecord(
        id=task_id,
        created_at=now,
        user_message=user_message,
        status=status,
        final_answer=final_answer,
        trace_json=json.dumps(trace),
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        error_message=error_message,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    append_jsonl_audit(row)
    log_task_metrics(
        task_id=task_id,
        status=status,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )
    return row
