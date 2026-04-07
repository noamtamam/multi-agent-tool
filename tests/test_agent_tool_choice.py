"""
Integration tests focused specifically on tool selection.

These tests use the real OpenAI API (OPENAI_API_KEY must be set).
Assertions are intentionally non-brittle: they validate that the agent chose the
expected tool at least once, not the exact wording of outputs.
"""

from __future__ import annotations

import pytest

from app.agent import run_agent_task
from app.config import settings


def _has_openai_key() -> bool:
    return bool(settings.openai_api_key and settings.openai_api_key.strip())


requires_openai = pytest.mark.skipif(
    not _has_openai_key(),
    reason="OPENAI_API_KEY not set — add it to .env or the environment to run these tests",
)


@pytest.mark.parametrize(
    ("user_message", "expected_tool"),
    [
        (
            "What's the current weather in Tokyo right now?",
            "weather",
        ),
        (
            "Is it raining in London right now?",
            "weather",
        ),
        (
            "What's the temperature in New York City right now?",
            "weather",
        ),
        (
            "Current weather in Paris?",
            "weather",
        ),
        (
            "How windy is it in Chicago right now?",
            "weather",
        ),
        (
            "Do I need an umbrella in Singapore today?",
            "weather",
        ),
        (
            "Convert 5 miles to kilometers.",
            "unit_converter",
        ),
        (
            "How many kilograms is 180 pounds?",
            "unit_converter",
        ),
        (
            "Turn 72 inches into feet.",
            "unit_converter",
        ),
        (
            "Convert 3.5 liters to milliliters.",
            "unit_converter",
        ),
        (
            "How many meters are in 2.2 kilometers?",
            "unit_converter",
        ),
        (
            "Convert 25 Celsius to Fahrenheit.",
            "unit_converter",
        ),
        (
            "Convert 0 Fahrenheit to Celsius.",
            "unit_converter",
        ),
        (
            "What's 1.5 GB in MB?",
            "unit_converter",
        ),
        (
            "Convert 10 EUR to JPY using today's exchange rate.",
            "unit_converter",
        ),
        (
            "If I have 2500 grams, how many kilograms is that?",
            "unit_converter",
        ),
        (
            "Convert 100 USD to EUR using today's exchange rate.",
            "unit_converter",
        ),
        (
            "Search the web for 'FastAPI dependency injection' and summarize the top 3 results.",
            "web_search",
        ),
        (
            "Who owns Twitter?",
            "web_search",
        ),
        (
            "What's the latest version of Python?",
            "web_search",
        ),
        (
            "Who is the CEO of OpenAI?",
            "web_search",
        ),
        (
            "When was FastAPI first released?",
            "web_search",
        ),
        (
            "What is the capital of Australia?",
            "web_search",
        ),
        (
            "Find me a reliable source that explains what JSONL is.",
            "web_search",
        ),
        (
            "What does HTTP status code 418 mean?",
            "web_search",
        ),
        (
            "Compute 12345**2 and reply with only the number.",
            "calculator",
        ),
        (
            "How much is two plus 7?",
            "calculator",
        ),
        (
            "What's 15% of 260?",
            "calculator",
        ),
        (
            "If I buy 3 items for $19.99 each, what's the total before tax?",
            "calculator",
        ),
        (
            "What is (48/6) * (3+5)?",
            "calculator",
        ),
        (
            "Can you calculate 7 factorial?",
            "calculator",
        ),
        (
            "What's the square root of 144?",
            "calculator",
        ),
        (
            "I have 2.5 hours. How many minutes is that?",
            "calculator",
        ),
    ],
)
@requires_openai
def test_agent_selects_expected_tool_for_general_request(
    user_message: str,
    expected_tool: str,
) -> None:
    out = run_agent_task(user_message)
    tool_calls = [s for s in out["trace"] if s.get("type") == "tool_call"]
    assert len(tool_calls) >= 1
    assert any(s.get("tool_name") == expected_tool for s in tool_calls)

