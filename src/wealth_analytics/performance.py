"""How a client's portfolio has performed, valued at each day's closing prices."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from math import prod

from wealth_analytics.price_history import PriceHistory
from wealth_analytics.transaction import Transaction


@dataclass(frozen=True)
class DailyValue:
    """The portfolio at one day's close."""

    day: date
    market_value: float  # what the shares held are worth
    net_invested: float  # money put in by purchases minus money taken out by sales
    daily_return: float  # change in value of the shares held overnight (0.01 = 1%)

    @property
    def total_gain(self) -> float:
        """Profit so far, realized or not: what it is worth minus what went in."""
        return self.market_value - self.net_invested


class Performance:
    """A client's portfolio replayed day by day, from their first trade onwards.

    Trades are assumed to happen at the day's close, so the money they move is
    a cash flow at the end of that day, not part of the day's return.
    """

    def __init__(self, transactions: Iterable[Transaction], prices: PriceHistory):
        self._prices = prices
        self._daily_values = self._value_each_day(
            sorted(transactions, key=lambda t: t.trade_date)
        )

    @property
    def daily_values(self) -> list[DailyValue]:
        """One entry per trading day, oldest first."""
        return list(self._daily_values)

    def time_weighted_return(
        self, start: date | None = None, end: date | None = None
    ) -> float:
        """Compounded return from the close on start to the close on end.

        Each day's return only measures how the investments moved, so money
        added or withdrawn does not count as performance (0.21 = 21%).
        """
        return (
            prod(
                1 + value.daily_return
                for value in self._daily_values
                if (start is None or value.day > start)
                and (end is None or value.day <= end)
            )
            - 1
        )

    def cumulative_returns(self) -> list[tuple[date, float]]:
        """The time-weighted return from the first trade up to each day."""
        growth = 1.0
        returns = []
        for value in self._daily_values:
            growth *= 1 + value.daily_return
            returns.append((value.day, growth - 1))
        return returns

    def _value_each_day(self, trades: list[Transaction]) -> list[DailyValue]:
        if not trades:
            return []

        holdings: dict[str, float] = defaultdict(float)
        net_invested = previous_value = 0.0
        next_trade = 0
        values = []
        for day in self._prices.trading_days():
            if day < trades[0].trade_date:
                continue

            cash_flow = 0.0
            while next_trade < len(trades) and trades[next_trade].trade_date <= day:
                trade = trades[next_trade]
                holdings[trade.ticker] += trade.signed_quantity
                cash_flow += trade.signed_quantity * trade.price
                next_trade += 1

            market_value = sum(
                quantity * self._prices.close_on(ticker, day)
                for ticker, quantity in holdings.items()
                if quantity
            )
            daily_return = (
                (market_value - cash_flow) / previous_value - 1
                if previous_value
                else 0.0
            )
            net_invested += cash_flow
            values.append(DailyValue(day, market_value, net_invested, daily_return))
            previous_value = market_value
        return values
