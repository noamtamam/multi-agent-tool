"""
Integration tests for the agent on known tasks.

Uses the real OpenAI API (OPENAI_API_KEY in environment or .env). Tool execution
(calculator, unit_converter, etc.) runs for real; assertions allow normal LLM variance.
"""

import pytest

from app.agent import run_agent_task
from app.config import settings


def _has_openai_key() -> bool:
    return bool(settings.openai_api_key and settings.openai_api_key.strip())


requires_openai = pytest.mark.skipif(
    not _has_openai_key(),
    reason="OPENAI_API_KEY not set — add it to .env or the environment to run these tests",
)


@requires_openai
def test_calculator_known_task_final_answer_matches_evaluated_expression() -> None:
    """Task: arithmetic (2+3)*4 → final answer should include 20."""
    out = run_agent_task("What is (2+3)*4? Reply with the numeric result.")

    assert "20" in out["final_answer"]
    assert out["total_tokens"] > 0
    assert out["prompt_tokens"] >= 0
    assert out["completion_tokens"] >= 0


@requires_openai
def test_trace_records_calculator_tool_and_numeric_result() -> None:
    """Trace should include a calculator tool step whose result is 20."""
    out = run_agent_task(
        "Use the calculator tool only: compute (2+3)*4. Do not guess; call calculator."
    )

    tool_steps = [s for s in out["trace"] if s.get("type") == "tool_call"]
    assert len(tool_steps) >= 1
    calc_steps = [s for s in tool_steps if s.get("tool_name") == "calculator"]
    assert len(calc_steps) >= 1
    assert calc_steps[0]["result"] == "20"


@requires_openai
def test_unit_conversion_km_to_meters_known_output() -> None:
    """Task: 1 km to meters → conversion should yield 1000 m."""
    out = run_agent_task(
        "Use the unit_converter tool: convert 1 km to meters. Then state the answer in plain text."
    )

    tool_steps = [s for s in out["trace"] if s.get("type") == "tool_call"]
    uc = [s for s in tool_steps if s.get("tool_name") == "unit_converter"]
    assert len(uc) >= 1
    assert "1000" in uc[0]["result"]
    assert "1000" in out["final_answer"]


@requires_openai
def test_trace_ends_with_usage_summary_and_positive_latency() -> None:
    """Observability: last step is usage; latency is recorded and non-negative."""
    out = run_agent_task("Say hello in one word only, no tools.")

    assert out["trace"][-1]["type"] == "usage"
    assert out["trace"][-1]["total_tokens"] >= 0
    assert out["latency_ms"] >= 0.0
    assert out["total_tokens"] == out["trace"][-1]["total_tokens"]


@requires_openai
def test_multi_tool_sequence_both_results_in_trace() -> None:
    """Workflow: calculator then unit converter; both tool results should appear."""
    out = run_agent_task(
        "First use the calculator to compute 2**10. "
        "Then use unit_converter to convert that many meters to kilometers (length). "
        "Summarize both results in your final answer."
    )

    names = [s["tool_name"] for s in out["trace"] if s.get("type") == "tool_call"]
    assert "calculator" in names
    assert "unit_converter" in names
    calc = next(s for s in out["trace"] if s.get("tool_name") == "calculator")
    assert calc["result"] == "1024"
    combined = out["final_answer"] + " ".join(
        str(s.get("result", "")) for s in out["trace"] if s.get("type") == "tool_call"
    )
    assert "1024" in combined
    assert "1.024" in combined or "1.024" in out["final_answer"]
