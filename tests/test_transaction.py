"""Tests for the Transaction class: trade amounts, direction and input validation."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from wealth_analytics.transaction import Side, Transaction


def make_transaction(**overrides: object) -> Transaction:
    """Build a valid RY purchase, replacing any fields given in overrides."""
    fields: dict[str, object] = {
        "trade_date": date(2026, 3, 2),
        "ticker": "RY",
        "side": Side.BUY,
        "quantity": 200,
        "price": 150.00,
    }
    fields.update(overrides)
    return Transaction(**fields)


# --- Calculations -----------------------------------------------------------


def test_amount_is_quantity_times_price() -> None:
    assert make_transaction().amount == 30_000


def test_signed_quantity_is_positive_for_a_buy() -> None:
    assert make_transaction(side=Side.BUY).signed_quantity == 200


def test_signed_quantity_is_negative_for_a_sell() -> None:
    assert make_transaction(side=Side.SELL).signed_quantity == -200


# --- Validation -------------------------------------------------------------


def test_blank_ticker_is_rejected() -> None:
    with pytest.raises(ValueError):
        make_transaction(ticker="  ")


@pytest.mark.parametrize("field_name", ["quantity", "price"])
@pytest.mark.parametrize("bad_value", [0, -5])
def test_quantity_and_price_must_be_positive(field_name: str, bad_value: int) -> None:
    with pytest.raises(ValueError):
        make_transaction(**{field_name: bad_value})


def test_side_must_be_a_side() -> None:
    with pytest.raises(TypeError):
        make_transaction(side="BUY")


def test_trade_date_must_be_a_date() -> None:
    with pytest.raises(TypeError):
        make_transaction(trade_date="2026-03-02")


def test_transaction_cannot_be_changed_after_creation() -> None:
    transaction = make_transaction()
    with pytest.raises(FrozenInstanceError):
        transaction.quantity = 999
