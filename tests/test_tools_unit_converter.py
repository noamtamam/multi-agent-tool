from __future__ import annotations

from typing import Any

import pytest

import app.tools.unit_converter as uc


def test_convert_units_length_km_to_m() -> None:
    out = uc.convert_units(1, "km", "m", category="length")
    assert "1.0 km = 1000 m" in out or "1 km = 1000 m" in out


def test_convert_units_temperature_c_to_f() -> None:
    out = uc.convert_units(0, "degC", "degF", category="temperature")
    assert "0.0 degC = " in out
    assert "32" in out


def test_convert_units_value_must_be_number() -> None:
    out = uc.convert_units("nope", "m", "km")  # type: ignore[arg-type]
    assert out == "Error: value must be a number"


def test_convert_units_currency_same_code_no_network() -> None:
    out = uc.convert_units(12.5, "USD", "USD", category="currency")
    assert out == "12.5 USD = 12.5 USD"


def test_convert_units_currency_uses_rate(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {"rates": {"EUR": 0.5}}

    def fake_get(*_args: Any, **_kwargs: Any) -> FakeResp:
        return FakeResp()

    monkeypatch.setattr(uc.httpx, "get", fake_get)

    out = uc.convert_units(10, "USD", "EUR", category="currency")
    assert out.startswith("10.0 USD = ")
    assert " EUR " in out
    assert "(rate 0.5)" in out

