from app.tools import dispatch_tool_call


def test_dispatch_tool_call_invalid_json_returns_error() -> None:
    out = dispatch_tool_call("calculator", "{not json")
    assert out.startswith("Error: invalid tool arguments JSON")


def test_dispatch_tool_call_unknown_tool_returns_error() -> None:
    out = dispatch_tool_call("does_not_exist", "{}")
    assert out.startswith("Error: unknown tool")


def test_dispatch_tool_call_tool_execution_exception_is_caught() -> None:
    # unit_converter will throw if "value" missing; dispatch should catch and wrap
    out = dispatch_tool_call("unit_converter", "{}")
    assert out.startswith("Error: tool execution failed")

