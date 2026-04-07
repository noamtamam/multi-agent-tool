import asyncio
import json
from collections.abc import Callable
from typing import Any

from app.tools.calculator import calculator_openai_schema, evaluate_expression
from app.tools.unit_converter import convert_units, unit_converter_openai_schema
from app.tools.weather import fetch_weather, weather_openai_schema
from app.tools.web_search import search_web, web_search_openai_schema


def get_openai_tool_definitions() -> list[dict[str, Any]]:
    return [
        calculator_openai_schema(),
        weather_openai_schema(),
        web_search_openai_schema(),
        unit_converter_openai_schema(),
    ]


def _run_tool(name: str, arguments: dict[str, Any]) -> str:
    if name == "calculator":
        return evaluate_expression(str(arguments.get("expression", "")))
    if name == "weather":
        city = str(arguments.get("city", ""))
        return asyncio.run(fetch_weather(city))
    if name == "web_search":
        q = str(arguments.get("query", ""))
        mr = arguments.get("max_results", 5)
        try:
            mr = int(mr)
        except (TypeError, ValueError):
            mr = 5
        return search_web(q, max_results=mr)
    if name == "unit_converter":
        return convert_units(
            float(arguments["value"]),
            str(arguments.get("from_unit", "")),
            str(arguments.get("to_unit", "")),
            str(arguments.get("category", "auto")),
        )
    return f"Error: unknown tool {name}"


def dispatch_tool_call(name: str, arguments_json: str) -> str:
    try:
        args = json.loads(arguments_json) if arguments_json else {}
    except json.JSONDecodeError as e:
        return f"Error: invalid tool arguments JSON — {e}"
    try:
        return _run_tool(name, args)
    except Exception as e:
        return f"Error: tool execution failed — {e}"


TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    "calculator": lambda **kw: evaluate_expression(str(kw.get("expression", ""))),
    "weather": lambda **kw: asyncio.run(fetch_weather(str(kw.get("city", "")))),
    "web_search": lambda **kw: search_web(str(kw.get("query", "")), int(kw.get("max_results", 5) or 5)),
    "unit_converter": lambda **kw: convert_units(
        float(kw["value"]),
        str(kw.get("from_unit", "")),
        str(kw.get("to_unit", "")),
        str(kw.get("category", "auto")),
    ),
}

__all__ = [
    "TOOL_REGISTRY",
    "dispatch_tool_call",
    "get_openai_tool_definitions",
]
