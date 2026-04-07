"""Convert units: length, weight, temperature via pint; currency via Frankfurter API."""

import httpx
from pint import UnitRegistry

_ureg = UnitRegistry()


def convert_units(
    value: float,
    from_unit: str,
    to_unit: str,
    category: str = "auto",
) -> str:
    """
    category: auto | length | weight | temperature | currency
    For currency, from_unit/to_unit are ISO codes (USD, EUR, GBP, ...).
    """
    fu = (from_unit or "").strip().lower()
    tu = (to_unit or "").strip().lower()
    cat = (category or "auto").strip().lower()
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "Error: value must be a number"

    if cat == "currency" or (cat == "auto" and len(fu) == 3 and len(tu) == 3 and fu.isalpha() and tu.isalpha()):
        return _convert_currency(v, fu, tu)

    try:
        q_from = _ureg.Quantity(v, fu)
        q_to = q_from.to(tu)
        mag = float(q_to.magnitude)
        if mag == int(mag):
            mag_s = str(int(mag))
        else:
            mag_s = f"{mag:.12g}"
        return f"{v} {fu} = {mag_s} {tu}"
    except Exception as e:
        return f"Error: conversion failed — {e}"


def _convert_currency(amount: float, from_code: str, to_code: str) -> str:
    if from_code == to_code:
        return f"{amount} {from_code} = {amount} {to_code}"
    try:
        r = httpx.get(
            "https://api.frankfurter.app/latest",
            params={"from": from_code, "to": to_code},
            timeout=15.0,
        )
        r.raise_for_status()
        data = r.json()
        rates = data.get("rates") or {}
        rate = rates.get(to_code)
        if rate is None:
            return f"Error: no rate for {from_code} → {to_code}"
        out = amount * float(rate)
        return f"{amount} {from_code} = {out:.4f} {to_code} (rate {rate})"
    except Exception as e:
        return f"Error: currency API failed — {e}"


def unit_converter_openai_schema() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "unit_converter",
            "description": (
                "Convert between units. Categories: length (m, ft, km), weight (kg, lb), "
                "temperature (degC, degF, kelvin), currency (3-letter ISO: USD, EUR, GBP)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {"type": "number", "description": "Numeric amount to convert."},
                    "from_unit": {"type": "string", "description": "Source unit or currency code."},
                    "to_unit": {"type": "string", "description": "Target unit or currency code."},
                    "category": {
                        "type": "string",
                        "description": "auto, length, weight, temperature, or currency.",
                    },
                },
                "required": ["value", "from_unit", "to_unit"],
            },
        },
    }
