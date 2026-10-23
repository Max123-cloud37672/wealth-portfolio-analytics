"""Daily closing prices for many tickers, with lookups that handle weekends."""

from bisect import bisect_right
from collections.abc import Mapping
from datetime import date


class PriceHistory:
    """Closing prices by ticker and day, e.g. RY closed at $150.25 on 2 March 2026."""

    def __init__(self, closes: Mapping[str, Mapping[date, float]]) -> None:
        self._closes = {ticker: dict(by_day) for ticker, by_day in closes.items()}
        self._days = {ticker: sorted(by_day) for ticker, by_day in closes.items()}

    def close_on(self, ticker: str, day: date) -> float:
        """The latest close on or before the given day (Friday's close on a Sunday)."""
        days = self._days.get(ticker)
        if not days:
            raise ValueError(f"No prices for {ticker}")
        position = bisect_right(days, day)
        if position == 0:
            raise ValueError(f"No price for {ticker} on or before {day}")
        return self._closes[ticker][days[position - 1]]

    def trading_days(self) -> list[date]:
        """Every day that has a price for at least one ticker, oldest first."""
        return sorted({day for days in self._days.values() for day in days})
