"""Multi-step tool-calling agent with a structured trace (observable reasoning loop)."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

from openai import OpenAI

from app.config import settings
from app.tools import dispatch_tool_call, get_openai_tool_definitions

SYSTEM_PROMPT = """You are a careful assistant that solves user tasks step by step.

You have tools for:
- calculator (math)
- unit_converter (unit + currency conversion)
- weather (current weather by city)
- web_search (up-to-date facts)

Tool-use policy:
- You MUST call at least one tool whenever the user's request is answerable using the available tools. Do not answer "from memory" in those cases.
- Use calculator for arithmetic/math phrased in words or symbols.
- Use unit_converter for any unit conversion requests (length/weight/temperature/currency) and also for data-size conversions (KB/MB/GB/TB).
- Use weather for any "current weather / raining / temperature / wind" questions about a place.
- Use web_search for factual questions (who/what/when/where/why) or anything that could be outdated; even if you think you know the answer, verify via web_search.
- For currency conversions and anything mentioning "today", "latest", "current", or "right now", always use the relevant tool.
- If a tool call fails, say briefly what happened and try another tool if appropriate; otherwise answer with best effort and clearly label uncertainty.

Return a concise final answer once you have enough information."""


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_agent_task(
    user_message: str,
    *,
    max_rounds: int = 12,
    client: OpenAI | None = None,
) -> dict[str, Any]:
    """
    Run the agent until the model returns text without tool calls or max_rounds is hit.
    Returns: final_answer, trace (list of dicts), usage totals, latency_ms.
    """
    if not (settings.openai_api_key or client):
        raise RuntimeError("OPENAI_API_KEY is not set and no client was provided")

    client = client or OpenAI(api_key=settings.openai_api_key)
    tools = get_openai_tool_definitions()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    trace: list[dict[str, Any]] = []
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    t0 = time.perf_counter()

    for round_idx in range(max_rounds):
        resp = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        u = resp.usage
        if u:
            prompt_tokens += u.prompt_tokens or 0
            completion_tokens += u.completion_tokens or 0
            total_tokens += u.total_tokens or 0

        msg = resp.choices[0].message
        if msg.content:
            trace.append(
                {
                    "type": "reasoning",
                    "role": "assistant",
                    "content": msg.content,
                    "round": round_idx,
                    "timestamp": _iso_now(),
                }
            )

        if not msg.tool_calls:
            latency_ms = (time.perf_counter() - t0) * 1000
            trace.append(
                {
                    "type": "usage",
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "timestamp": _iso_now(),
                }
            )
            return {
                "final_answer": (msg.content or "").strip(),
                "trace": trace,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "latency_ms": latency_ms,
            }

        messages.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments or "{}"},
                    }
                    for tc in msg.tool_calls
                ],
            }
        )

        for tc in msg.tool_calls:
            name = tc.function.name
            raw_args = tc.function.arguments or "{}"
            result = dispatch_tool_call(name, raw_args)
            try:
                args_dict = json.loads(raw_args) if raw_args.strip() else {}
            except json.JSONDecodeError:
                args_dict = {"_raw": raw_args}
            trace.append(
                {
                    "type": "tool_call",
                    "tool_name": name,
                    "arguments": args_dict,
                    "result": result,
                    "timestamp": _iso_now(),
                    "round": round_idx,
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                }
            )

    latency_ms = (time.perf_counter() - t0) * 1000
    trace.append(
        {
            "type": "usage",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "timestamp": _iso_now(),
        }
    )
    return {
        "final_answer": "Error: maximum reasoning rounds exceeded without a final reply.",
        "trace": trace,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "latency_ms": latency_ms,
    }
