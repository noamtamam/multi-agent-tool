from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    task: str = Field(..., min_length=1, description="Natural language task for the agent")


class TraceStepBase(BaseModel):
    type: str
    timestamp: str | None = None


class ReasoningStep(TraceStepBase):
    type: Literal["reasoning"] = "reasoning"
    role: str
    content: str | None = None


class ToolCallStep(TraceStepBase):
    type: Literal["tool_call"] = "tool_call"
    tool_name: str
    arguments: dict[str, Any]
    result: str
    error: str | None = None


class UsageStep(TraceStepBase):
    type: Literal["usage"] = "usage"
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class TaskResponse(BaseModel):
    task_id: str
    status: str
    final_answer: str | None
    trace: list[dict[str, Any]]
    latency_ms: float | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    error: str | None = None


class TaskStoredResponse(BaseModel):
    task_id: str
    created_at: datetime
    status: str
    user_message: str
    final_answer: str | None
    trace: list[dict[str, Any]]
    latency_ms: float | None
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    error: str | None
