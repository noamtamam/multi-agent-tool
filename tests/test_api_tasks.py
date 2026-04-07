"""API tests with mocked agent (no OpenAI)."""

from __future__ import annotations

from typing import Any

import pytest


def test_create_task_persists_and_get_returns_same(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(msg: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "final_answer": "42",
            "trace": [
                {"type": "usage", "prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
            ],
            "prompt_tokens": 1,
            "completion_tokens": 2,
            "total_tokens": 3,
            "latency_ms": 12.5,
        }

    monkeypatch.setattr("app.main.run_agent_task", fake_run)

    r = api_client.post("/tasks", json={"task": "what is the answer"})
    assert r.status_code == 201
    body = r.json()
    task_id = body["task_id"]
    assert body["status"] == "completed"
    assert body["final_answer"] == "42"
    assert body["latency_ms"] == 12.5
    assert body["prompt_tokens"] == 1
    assert body["completion_tokens"] == 2
    assert body["total_tokens"] == 3
    assert body["user_message"] == "what is the answer"
    assert len(body["trace"]) >= 1

    r2 = api_client.get(f"/tasks/{task_id}")
    assert r2.status_code == 200
    assert r2.json() == body


def test_get_task_not_found(api_client) -> None:
    r = api_client.get("/tasks/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_create_task_failed_persisted(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(_msg: str, **kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("no api key")

    monkeypatch.setattr("app.main.run_agent_task", boom)

    r = api_client.post("/tasks", json={"task": "x"})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "failed"
    assert body["error"] == "no api key"
    assert body["final_answer"] is None

    r2 = api_client.get(f"/tasks/{body['task_id']}")
    assert r2.status_code == 200
    assert r2.json()["status"] == "failed"
