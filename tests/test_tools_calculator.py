import pytest

from app.tools.calculator import evaluate_expression


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        ("(2+3)*4", "20"),
        ("2**10", "1024"),
        ("5/2", "2.5"),
        ("5//2", "2"),
        ("-3 + 10", "7"),
        ("2%3", "2"),
        ("0.1 + 0.2", "0.3"),
    ],
)
def test_evaluate_expression_valid(expr: str, expected: str) -> None:
    assert evaluate_expression(expr) == expected


@pytest.mark.parametrize(
    "expr",
    [
        "",
        "   ",
        "2+",
        "hello",
        "__import__('os').system('whoami')",
        "abs(-1)",
        "a + 1",
        "[1,2,3]",
        "{'x': 1}",
        "(lambda: 1)()",
    ],
)
def test_evaluate_expression_rejects_unsafe_or_invalid(expr: str) -> None:
    out = evaluate_expression(expr)
    assert out.startswith("Error:")


def test_evaluate_expression_divide_by_zero() -> None:
    out = evaluate_expression("1/0")
    assert out.startswith("Error:")

