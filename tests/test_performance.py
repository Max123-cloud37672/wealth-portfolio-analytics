"""Tests for Performance: daily values, gains and time-weighted return (TWR)."""

from datetime import date

import pytest

from wealth_analytics.performance import Performance
from wealth_analytics.price_history import PriceHistory
from wealth_analytics.transaction import Side, Transaction

DAY_1, DAY_2, DAY_3, DAY_4 = (date(2026, 3, day) for day in (2, 3, 4, 5))


def prices(*closes: float) -> PriceHistory:
    """One ticker, X, with the given closes on days 1, 2, 3, ..."""
    days = (DAY_1, DAY_2, DAY_3, DAY_4)
    return PriceHistory({"X": dict(zip(days, closes, strict=False))})


def buy(day: date, quantity: float, price: float) -> Transaction:
    return Transaction(day, "X", Side.BUY, quantity, price)


def sell(day: date, quantity: float, price: float) -> Transaction:
    return Transaction(day, "X", Side.SELL, quantity, price)


# --- Daily values -----------------------------------------------------------


def test_no_trades_means_no_history() -> None:
    performance = Performance([], prices(10, 11))

    assert performance.daily_values == []
    assert performance.time_weighted_return() == 0


def test_history_starts_on_the_first_trade() -> None:
    performance = Performance([buy(DAY_2, 100, 11)], prices(10, 11, 12))

    assert [value.day for value in performance.daily_values] == [DAY_2, DAY_3]


def test_market_value_follows_the_closing_price() -> None:
    performance = Performance([buy(DAY_1, 100, 10)], prices(10, 11, 12))

    assert [v.market_value for v in performance.daily_values] == [1_000, 1_100, 1_200]


def test_total_gain_is_market_value_minus_net_invested() -> None:
    performance = Performance([buy(DAY_1, 100, 10)], prices(10, 11, 12))

    last = performance.daily_values[-1]
    assert last.net_invested == 1_000
    assert last.total_gain == 200


def test_a_sale_takes_money_out_and_keeps_the_gain() -> None:
    performance = Performance(
        [buy(DAY_1, 100, 10), sell(DAY_2, 100, 12)], prices(10, 12)
    )

    last = performance.daily_values[-1]
    assert last.market_value == 0
    assert last.net_invested == -200  # put in 1,000, took out 1,200
    assert last.total_gain == 200


# --- Time-weighted return ---------------------------------------------------


def test_twr_compounds_the_daily_returns() -> None:
    performance = Performance([buy(DAY_1, 100, 10)], prices(10, 11, 12))

    assert performance.time_weighted_return() == pytest.approx(0.20)


def test_adding_money_does_not_count_as_return() -> None:
    # +10%, then the client adds $1,100, then +10% again: TWR is 1.1 x 1.1 - 1 = 21%,
    # even though the simple gain is only 320 / 2,100 = 15.2%.
    performance = Performance(
        [buy(DAY_1, 100, 10), buy(DAY_2, 100, 11)], prices(10, 11, 12.1)
    )

    assert performance.time_weighted_return() == pytest.approx(0.21)


def test_selling_everything_locks_in_the_return() -> None:
    performance = Performance(
        [buy(DAY_1, 100, 10), sell(DAY_2, 100, 12)], prices(10, 12, 50)
    )

    assert performance.time_weighted_return() == pytest.approx(0.20)


def test_twr_can_cover_part_of_the_history() -> None:
    performance = Performance([buy(DAY_1, 100, 10)], prices(10, 11, 12, 15))

    assert performance.time_weighted_return(start=DAY_2, end=DAY_3) == pytest.approx(
        12 / 11 - 1
    )


def test_cumulative_returns_give_the_twr_to_date_each_day() -> None:
    performance = Performance([buy(DAY_1, 100, 10)], prices(10, 11, 12))

    assert performance.cumulative_returns() == [
        (DAY_1, 0),
        (DAY_2, pytest.approx(0.10)),
        (DAY_3, pytest.approx(0.20)),
    ]
