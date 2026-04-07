"""HTTP API: create tasks (agent run) and retrieve stored results."""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.agent import run_agent_task
from app.db import get_session, init_db
from app.models import TaskRecord
from app.schemas import TaskCreateRequest, TaskStoredResponse
from app.task_store import row_to_stored_response, save_task_record

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
    )
    init_db()
    yield


app = FastAPI(title="Multi-agent tool", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/tasks", response_model=TaskStoredResponse, status_code=201)
@app.post("/task", response_model=TaskStoredResponse, status_code=201)  # backwards-compatible alias
def create_task(
    body: TaskCreateRequest,
    db: Session = Depends(get_session),
) -> TaskStoredResponse:
    task_id = str(uuid.uuid4())
    try:
        out = run_agent_task(body.task)
    except Exception as e:
        logger.exception("task_failed task_id=%s", task_id)
        row = save_task_record(
            db,
            task_id=task_id,
            user_message=body.task,
            status="failed",
            final_answer=None,
            trace=[],
            latency_ms=None,
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            error_message=str(e),
        )
        return row_to_stored_response(row)

    row = save_task_record(
        db,
        task_id=task_id,
        user_message=body.task,
        status="completed",
        final_answer=out["final_answer"],
        trace=out["trace"],
        latency_ms=out["latency_ms"],
        prompt_tokens=out["prompt_tokens"],
        completion_tokens=out["completion_tokens"],
        total_tokens=out["total_tokens"],
        error_message=None,
    )
    return row_to_stored_response(row)


@app.get("/tasks/{task_id}", response_model=TaskStoredResponse)
def get_task(task_id: str, db: Session = Depends(get_session)) -> TaskStoredResponse:
    row = db.get(TaskRecord, task_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return row_to_stored_response(row)
