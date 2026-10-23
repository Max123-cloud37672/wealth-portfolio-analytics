"""Tests for the Portfolio class: replaying a client's trades into positions."""

from datetime import date

import pytest

from wealth_analytics.portfolio import Portfolio
from wealth_analytics.transaction import Side, Transaction


def buy(ticker: str, quantity: float, price: float, day: int = 1) -> Transaction:
    """A purchase on the given day of March 2026."""
    return Transaction(date(2026, 3, day), ticker, Side.BUY, quantity, price)


def sell(ticker: str, quantity: float, price: float, day: int = 1) -> Transaction:
    """A sale on the given day of March 2026."""
    return Transaction(date(2026, 3, day), ticker, Side.SELL, quantity, price)


def test_portfolio_with_no_trades_has_no_positions() -> None:
    portfolio = Portfolio([])

    assert portfolio.positions == {}
    assert portfolio.realized_gain == 0


def test_a_buy_opens_a_position() -> None:
    portfolio = Portfolio([buy("RY", 100, 10.00)])

    position = portfolio.positions["RY"]
    assert position.quantity == 100
    assert position.average_cost == 10.00


def test_two_buys_of_the_same_ticker_average_the_cost() -> None:
    portfolio = Portfolio([buy("RY", 100, 10.00, day=1), buy("RY", 100, 20.00, day=2)])

    assert portfolio.positions["RY"].quantity == 200
    assert portfolio.positions["RY"].average_cost == pytest.approx(15.00)


def test_a_partial_sell_reduces_the_position_and_records_the_gain() -> None:
    portfolio = Portfolio(
        [
            buy("RY", 100, 10.00, day=1),
            buy("RY", 100, 20.00, day=2),
            sell("RY", 50, 18.00, day=3),
        ]
    )

    assert portfolio.positions["RY"].quantity == 150
    assert portfolio.positions["RY"].average_cost == pytest.approx(15.00)
    assert portfolio.realized_gain == pytest.approx(150.00)  # (18 - 15) x 50


def test_selling_at_a_loss_records_a_negative_gain() -> None:
    portfolio = Portfolio([buy("RY", 100, 10.00, day=1), sell("RY", 100, 8.00, day=2)])

    assert portfolio.realized_gain == pytest.approx(-200.00)  # (8 - 10) x 100


def test_selling_everything_closes_the_position() -> None:
    portfolio = Portfolio([buy("RY", 100, 10.00, day=1), sell("RY", 100, 12.00, day=2)])

    assert "RY" not in portfolio.positions


def test_selling_more_than_is_held_is_rejected() -> None:
    with pytest.raises(ValueError):
        Portfolio([buy("RY", 100, 10.00, day=1), sell("RY", 101, 12.00, day=2)])


def test_selling_a_ticker_never_bought_is_rejected() -> None:
    with pytest.raises(ValueError):
        Portfolio([sell("RY", 10, 12.00)])


def test_trades_are_replayed_in_date_order() -> None:
    # The sale is listed first but happened after the purchase, so it is valid.
    portfolio = Portfolio([sell("RY", 40, 12.00, day=5), buy("RY", 100, 10.00, day=1)])

    assert portfolio.positions["RY"].quantity == 60


def test_each_ticker_is_tracked_separately() -> None:
    portfolio = Portfolio([buy("RY", 100, 10.00), buy("XIU", 50, 40.00)])

    assert portfolio.positions["RY"].quantity == 100
    assert portfolio.positions["XIU"].quantity == 50


def test_total_cost_basis_adds_up_all_positions() -> None:
    portfolio = Portfolio([buy("RY", 100, 10.00), buy("XIU", 50, 40.00)])

    assert portfolio.total_cost_basis == pytest.approx(3_000.00)  # 1,000 + 2,000
