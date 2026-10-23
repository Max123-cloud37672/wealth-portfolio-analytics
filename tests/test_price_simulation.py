"""Tests for the illustrative price simulation used to build the sample prices."""

import random
from datetime import date

import pytest

from wealth_analytics.price_simulation import simulate_closes, weekdays_between

DAYS = weekdays_between(date(2025, 1, 6), date(2025, 3, 28))  # Mon to Fri, 12 weeks
ANCHORS = {
    date(2025, 1, 6): 100.00,
    date(2025, 2, 12): 112.50,
    date(2025, 3, 28): 95.25,
}


def simulate(seed: int = 1) -> dict[date, float]:
    return simulate_closes(
        DAYS, ANCHORS, daily_volatility=0.02, rng=random.Random(seed)
    )


def test_weekdays_between_skips_weekends() -> None:
    days = weekdays_between(date(2025, 1, 3), date(2025, 1, 7))  # Fri to Tue

    assert days == [date(2025, 1, 3), date(2025, 1, 6), date(2025, 1, 7)]


def test_every_day_gets_a_price() -> None:
    assert list(simulate()) == DAYS


def test_prices_pass_exactly_through_the_anchors() -> None:
    closes = simulate()

    for day, price in ANCHORS.items():
        assert closes[day] == price


def test_prices_are_positive_and_rounded_to_cents() -> None:
    for price in simulate().values():
        assert price > 0
        assert price == round(price, 2)


def test_prices_move_between_anchors() -> None:
    closes = simulate()

    assert len(set(closes.values())) > len(ANCHORS)


def test_the_same_seed_gives_the_same_prices() -> None:
    assert simulate(seed=7) == simulate(seed=7)


def test_first_and_last_day_must_be_anchors() -> None:
    with pytest.raises(ValueError):
        simulate_closes(
            DAYS,
            {date(2025, 2, 12): 112.50},
            daily_volatility=0.02,
            rng=random.Random(),
        )


def test_anchors_must_be_trading_days() -> None:
    with pytest.raises(ValueError):
        simulate_closes(
            DAYS,
            {**ANCHORS, date(2025, 2, 15): 110.00},  # a Saturday
            daily_volatility=0.02,
            rng=random.Random(),
        )
