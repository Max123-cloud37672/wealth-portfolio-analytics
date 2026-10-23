"""Tests for the reporting helpers that turn portfolio results into dashboard tables."""

from datetime import date

import pytest

from wealth_analytics.performance import Performance
from wealth_analytics.portfolio import Portfolio
from wealth_analytics.price_history import PriceHistory
from wealth_analytics.reporting import (
    Period,
    allocation,
    holdings_table,
    period_start,
    return_comparison,
    summarize,
    transactions_table,
    value_history,
)
from wealth_analytics.security import AssetType, Security
from wealth_analytics.transaction import Side, Transaction

DAY_1, DAY_2, DAY_3 = date(2026, 3, 2), date(2026, 3, 3), date(2026, 3, 4)
PRICES = PriceHistory(
    {
        "RY": {DAY_1: 100.0, DAY_2: 110.0, DAY_3: 120.0},
        "XIU": {DAY_1: 40.0, DAY_2: 41.0, DAY_3: 42.0},
        "XBB": {DAY_1: 30.0, DAY_2: 30.0, DAY_3: 30.0},
    }
)
SECURITIES = {
    "RY": Security("RY", "Royal Bank of Canada", AssetType.STOCK, "Financials"),
    "XIU": Security("XIU", "iShares S&P/TSX 60", AssetType.ETF, "Canadian Equity"),
    "XBB": Security("XBB", "iShares Universe Bond", AssetType.ETF, "Fixed Income"),
}
TRADES = [
    Transaction(DAY_1, "RY", Side.BUY, 10, 100.0),
    Transaction(DAY_1, "XBB", Side.BUY, 20, 30.0),
    Transaction(DAY_2, "RY", Side.SELL, 5, 110.0),
]


# --- Periods ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("period", "expected"),
    [
        (Period.THREE_MONTHS, date(2026, 7, 23)),
        (Period.SIX_MONTHS, date(2026, 4, 23)),
        (Period.ONE_YEAR, date(2025, 10, 23)),
        (Period.YEAR_TO_DATE, date(2025, 12, 31)),
        (Period.ALL, None),
    ],
)
def test_period_start_counts_back_from_the_last_day(
    period: Period, expected: date | None
) -> None:
    assert period_start(period, last_day=date(2026, 10, 23)) == expected


def test_months_back_from_a_long_month_end_land_on_a_real_day() -> None:
    assert period_start(Period.THREE_MONTHS, last_day=date(2026, 5, 31)) == date(
        2026, 2, 28
    )


# --- Headline summary -------------------------------------------------------


def test_summary_over_all_time() -> None:
    summary = summarize(Performance(TRADES, PRICES), PRICES, start=None)

    # Day 3: 5 RY at 120 + 20 XBB at 30 = 1,200. Invested 1,000 + 600 - 550 = 1,050.
    assert summary.market_value == 1_200
    assert summary.net_invested == 1_050
    assert summary.gain == pytest.approx(150)
    assert summary.benchmark_return == pytest.approx(42 / 40 - 1)


def test_summary_over_a_period_only_counts_gains_inside_it() -> None:
    summary = summarize(Performance(TRADES, PRICES), PRICES, start=DAY_2)

    # Day 2 close: 5 RY at 110 + 600 = 1,150, invested 1,050. Day 3: 1,200, 1,050.
    assert summary.gain == pytest.approx(50)
    assert summary.period_return == pytest.approx(1_200 / 1_150 - 1)
    assert summary.benchmark_return == pytest.approx(42 / 41 - 1)


# --- Charts -----------------------------------------------------------------


def test_value_history_starts_at_the_period_start() -> None:
    history = value_history(Performance(TRADES, PRICES), start=DAY_2)

    assert list(history["Date"]) == [DAY_2, DAY_3]
    assert list(history["Market value"]) == [1_150, 1_200]
    assert list(history["Net invested"]) == [1_050, 1_050]


def test_return_comparison_starts_both_lines_at_zero() -> None:
    comparison = return_comparison(
        Performance(TRADES, PRICES), PRICES, start=DAY_2, benchmark="XIU"
    )

    assert comparison["Portfolio"].iloc[0] == 0
    assert comparison["Benchmark"].iloc[0] == 0
    assert comparison["Portfolio"].iloc[-1] == pytest.approx(1_200 / 1_150 - 1)
    assert comparison["Benchmark"].iloc[-1] == pytest.approx(42 / 41 - 1)


# --- Tables -----------------------------------------------------------------


def test_holdings_table_values_each_position_on_the_given_day() -> None:
    table = holdings_table(Portfolio(TRADES), SECURITIES, PRICES, DAY_3)

    ry = table.set_index("Ticker").loc["RY"]
    assert ry["Name"] == "Royal Bank of Canada"
    assert ry["Market value"] == 600  # 5 x 120
    assert ry["Gain"] == 100  # 600 - 5 x 100
    assert ry["Gain %"] == pytest.approx(0.20)
    assert ry["Weight"] == pytest.approx(0.50)  # 600 of 1,200


def test_holdings_table_lists_the_largest_position_first() -> None:
    table = holdings_table(Portfolio(TRADES), SECURITIES, PRICES, DAY_3)

    assert list(table["Ticker"]) == ["RY", "XBB"]  # 600 vs 600: ties keep ticker order


def test_allocation_adds_up_weights_by_category() -> None:
    table = holdings_table(Portfolio(TRADES), SECURITIES, PRICES, DAY_3)

    weights = allocation(table, by="Asset type")

    assert weights.to_dict() == {"Stock": pytest.approx(0.5), "ETF": pytest.approx(0.5)}


def test_transactions_table_lists_the_newest_trade_first() -> None:
    table = transactions_table(TRADES)

    assert list(table["Date"]) == [DAY_2, DAY_1, DAY_1]
    assert table["Amount"].iloc[0] == 550
    assert table["Side"].iloc[0] == "Sell"
