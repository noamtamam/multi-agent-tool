"""Safely evaluate arithmetic expressions using a restricted AST visitor."""

import ast
import operator
from typing import Any


_ALLOWED_BINOPS: dict[type[ast.operator], Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED_UNARY: dict[type[ast.unaryop], Any] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return float(node.value)
        raise ValueError("Only numeric constants are allowed")
    if isinstance(node, ast.BinOp):
        op = _ALLOWED_BINOPS.get(type(node.op))
        if op is None:
            raise ValueError(f"Operator not allowed: {type(node.op).__name__}")
        return op(_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        op = _ALLOWED_UNARY.get(type(node.op))
        if op is None:
            raise ValueError(f"Unary operator not allowed: {type(node.op).__name__}")
        return op(_eval_node(node.operand))
    if isinstance(node, ast.Expr):
        return _eval_node(node.value)
    raise ValueError(f"Expression node not allowed: {type(node).__name__}")


def evaluate_expression(expression: str) -> str:
    """
    Evaluate a mathematical expression containing +, -, *, /, //, %, ** and parentheses.
    No names, no function calls, no attribute access.
    """
    expr = expression.strip()
    if not expr:
        return "Error: empty expression"
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        return f"Error: invalid syntax — {e.msg}"
    try:
        result = _eval_node(tree.body)
        if result == int(result):
            return str(int(result))
        return str(round(result, 12)).rstrip("0").rstrip(".") if "." in str(result) else str(result)
    except (ValueError, ZeroDivisionError, TypeError, OverflowError) as e:
        return f"Error: {e}"


def calculator_openai_schema() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": (
                "Evaluate a mathematical expression safely. Use standard arithmetic: + - * / // % ** "
                "and parentheses. Example: '(2 + 3) * 7'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The arithmetic expression to evaluate.",
                    }
                },
                "required": ["expression"],
            },
        },
    }
