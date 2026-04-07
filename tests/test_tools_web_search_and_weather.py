from __future__ import annotations

import asyncio

import pytest

import app.tools.web_search as ws
from app.tools.weather import fetch_weather


def test_web_search_empty_query() -> None:
    assert ws.search_web("") == "Error: search query is required"


def test_web_search_clamps_max_results(monkeypatch: pytest.MonkeyPatch) -> None:
    # Replace DDGS with a deterministic fake so this test is offline + fast.
    class FakeDDGS:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def text(self, query: str, max_results: int = 5):
            assert query == "x"
            # Ensure clamping to <= 10 happened
            assert 1 <= max_results <= 10
            for i in range(max_results):
                yield {"title": f"t{i}", "body": "b", "href": f"http://e/{i}"}

    monkeypatch.setattr(ws, "DDGS", FakeDDGS)
    out = ws.search_web("x", max_results=999)
    assert out.startswith("1. ")
    assert "http://e/0" in out


def test_fetch_weather_requires_city() -> None:
    # Avoid async test plugin dependency; this path returns before any network call.
    out = asyncio.run(fetch_weather("   "))
    assert out == "Error: city name is required"

