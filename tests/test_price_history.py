"""Tests for PriceHistory: looking up closing prices, including on non-trading days."""

from datetime import date

import pytest

from wealth_analytics.price_history import PriceHistory

FRIDAY, MONDAY = date(2026, 3, 6), date(2026, 3, 9)
HISTORY = PriceHistory(
    {
        "RY": {MONDAY: 151.00, FRIDAY: 150.00},
        "XIU": {MONDAY: 40.00},
    }
)


def test_close_on_a_trading_day() -> None:
    assert HISTORY.close_on("RY", MONDAY) == 151.00


def test_a_weekend_uses_the_previous_close() -> None:
    assert HISTORY.close_on("RY", date(2026, 3, 8)) == 150.00  # Sunday


def test_a_day_before_the_first_price_is_rejected() -> None:
    with pytest.raises(ValueError):
        HISTORY.close_on("XIU", FRIDAY)


def test_an_unknown_ticker_is_rejected() -> None:
    with pytest.raises(ValueError):
        HISTORY.close_on("ZZZ", MONDAY)


def test_trading_days_combine_every_ticker_oldest_first() -> None:
    assert HISTORY.trading_days() == [FRIDAY, MONDAY]
