"""Tests for the Position class: average cost after buys and sells, and validation."""

import pytest

from wealth_analytics.position import Position


def make_position(**overrides: object) -> Position:
    """Build a valid position of 100 RY shares at $10, replacing any overrides."""
    fields: dict[str, object] = {"ticker": "RY", "quantity": 100, "average_cost": 10.00}
    fields.update(overrides)
    return Position(**fields)


# --- Calculations -----------------------------------------------------------


def test_cost_basis_is_quantity_times_average_cost() -> None:
    assert make_position().cost_basis == 1_000


def test_buying_more_averages_the_cost() -> None:
    position = make_position().after_buy(quantity=100, price=20.00)

    assert position.quantity == 200
    assert position.average_cost == pytest.approx(15.00)


def test_selling_reduces_quantity_but_keeps_average_cost() -> None:
    position = make_position().after_sell(quantity=40)

    assert position.quantity == 60
    assert position.average_cost == 10.00


# --- Validation -------------------------------------------------------------


def test_blank_ticker_is_rejected() -> None:
    with pytest.raises(ValueError):
        make_position(ticker="")


@pytest.mark.parametrize("field_name", ["quantity", "average_cost"])
def test_quantity_and_average_cost_must_be_positive(field_name: str) -> None:
    with pytest.raises(ValueError):
        make_position(**{field_name: 0})
