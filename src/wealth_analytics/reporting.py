"""Turning portfolio results into the tables and figures the dashboard shows.

Everything here is plain calculation (no Streamlit), so it can be tested on its own.
"""

from calendar import monthrange
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from enum import Enum

import pandas as pd

from wealth_analytics.performance import DailyValue, Performance
from wealth_analytics.portfolio import Portfolio
from wealth_analytics.price_history import PriceHistory
from wealth_analytics.security import Security
from wealth_analytics.transaction import Transaction


class Period(Enum):
    """The time ranges a viewer can pick."""

    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    YEAR_TO_DATE = "YTD"
    ONE_YEAR = "1Y"
    ALL = "All"


@dataclass(frozen=True)
class Summary:
    """Headline figures for one client over one period."""

    market_value: float  # at the end of the period
    net_invested: float  # at the end of the period
    gain: float  # earned inside the period, after allowing for money added or taken out
    period_return: float  # time-weighted return over the period (0.05 = 5%)
    benchmark_return: float  # the benchmark's price return over the same period


def period_start(period: Period, last_day: date) -> date | None:
    """The day whose close the period is measured from (None means since the start).

    YTD is measured from the last close of the previous year.
    """
    match period:
        case Period.THREE_MONTHS:
            return _months_before(last_day, 3)
        case Period.SIX_MONTHS:
            return _months_before(last_day, 6)
        case Period.ONE_YEAR:
            return _months_before(last_day, 12)
        case Period.YEAR_TO_DATE:
            return date(last_day.year - 1, 12, 31)
        case Period.ALL:
            return None


def summarize(
    performance: Performance,
    prices: PriceHistory,
    start: date | None,
    benchmark: str = "XIU",
) -> Summary:
    """Headline figures from the close on start (or the first trade) to the last day."""
    values = performance.daily_values
    end = values[-1]
    opening = _value_on(values, start)
    base_day = opening.day if opening else values[0].day

    return Summary(
        market_value=end.market_value,
        net_invested=end.net_invested,
        gain=end.total_gain - (opening.total_gain if opening else 0.0),
        period_return=performance.time_weighted_return(start=start),
        benchmark_return=prices.close_on(benchmark, end.day)
        / prices.close_on(benchmark, base_day)
        - 1,
    )


def value_history(performance: Performance, start: date | None) -> pd.DataFrame:
    """Market value and net invested at each day's close from start onwards."""
    return pd.DataFrame(
        [
            {
                "Date": value.day,
                "Market value": value.market_value,
                "Net invested": value.net_invested,
            }
            for value in performance.daily_values
            if start is None or value.day >= start
        ]
    )


def return_comparison(
    performance: Performance,
    prices: PriceHistory,
    start: date | None,
    benchmark: str = "XIU",
) -> pd.DataFrame:
    """Portfolio and benchmark returns since start, measured from the same close."""
    cumulative = performance.cumulative_returns()
    opening = [growth for day, growth in cumulative if start and day <= start]
    base_growth = 1 + opening[-1] if opening else 1.0
    base_day = start if opening else cumulative[0][0]
    base_close = prices.close_on(benchmark, base_day)

    return pd.DataFrame(
        [
            {
                "Date": day,
                "Portfolio": (1 + growth) / base_growth - 1,
                "Benchmark": prices.close_on(benchmark, day) / base_close - 1,
            }
            for day, growth in cumulative
            if start is None or day >= start
        ]
    )


def holdings_table(
    portfolio: Portfolio,
    securities: Mapping[str, Security],
    prices: PriceHistory,
    day: date,
) -> pd.DataFrame:
    """One row per open position, valued at the close on day, largest first."""
    rows = []
    for ticker, position in portfolio.positions.items():
        security = securities[ticker]
        price = prices.close_on(ticker, day)
        market_value = position.quantity * price
        gain = market_value - position.cost_basis
        rows.append(
            {
                "Ticker": ticker,
                "Name": security.name,
                "Asset type": security.asset_type.value,
                "Sector": security.sector,
                "Quantity": position.quantity,
                "Average cost": position.average_cost,
                "Price": price,
                "Cost basis": position.cost_basis,
                "Market value": market_value,
                "Gain": gain,
                "Gain %": gain / position.cost_basis,
            }
        )

    table = pd.DataFrame(rows)
    table["Weight"] = table["Market value"] / table["Market value"].sum()
    return table.sort_values(
        ["Market value", "Ticker"], ascending=[False, True], ignore_index=True
    )


def allocation(holdings: pd.DataFrame, by: str) -> pd.Series:
    """Share of market value in each category of the given column, largest first."""
    return holdings.groupby(by)["Weight"].sum().sort_values(ascending=False)


def transactions_table(transactions: Iterable[Transaction]) -> pd.DataFrame:
    """Every trade, newest first (same-day trades keep their recorded order)."""
    rows = [
        {
            "Date": trade.trade_date,
            "Ticker": trade.ticker,
            "Side": trade.side.value,
            "Quantity": trade.quantity,
            "Price": trade.price,
            "Amount": trade.amount,
        }
        for trade in transactions
    ]
    return (
        pd.DataFrame(rows)
        .iloc[::-1]
        .sort_values("Date", ascending=False, kind="stable", ignore_index=True)
    )


def _months_before(day: date, months: int) -> date:
    """The same day of the month, months earlier (or that month's last day)."""
    month_index = day.year * 12 + day.month - 1 - months
    year, month = divmod(month_index, 12)
    month += 1
    return date(year, month, min(day.day, monthrange(year, month)[1]))


def _value_on(values: list[DailyValue], day: date | None) -> DailyValue | None:
    """The latest daily value on or before day, or None if there isn't one."""
    if day is None:
        return None
    earlier = [value for value in values if value.day <= day]
    return earlier[-1] if earlier else None
