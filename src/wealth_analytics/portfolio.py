"""A client's portfolio, worked out by replaying their trades in date order."""

from collections.abc import Iterable

from wealth_analytics.position import Position
from wealth_analytics.transaction import Side, Transaction


class Portfolio:
    """The positions and realized gain that result from a list of trades."""

    def __init__(self, transactions: Iterable[Transaction]) -> None:
        self._transactions = sorted(transactions, key=lambda t: t.trade_date)
        self._positions: dict[str, Position] = {}
        self._realized_gain = 0.0

        for transaction in self._transactions:
            if transaction.side is Side.BUY:
                self._apply_buy(transaction)
            else:
                self._apply_sell(transaction)

    @property
    def transactions(self) -> list[Transaction]:
        """All trades, oldest first."""
        return list(self._transactions)

    @property
    def positions(self) -> dict[str, Position]:
        """Open positions, keyed by ticker."""
        return dict(self._positions)

    @property
    def realized_gain(self) -> float:
        """Profit (positive) or loss (negative) locked in by sales so far."""
        return self._realized_gain

    @property
    def total_cost_basis(self) -> float:
        """Total amount invested in the open positions."""
        return sum(position.cost_basis for position in self._positions.values())

    def _apply_buy(self, transaction: Transaction) -> None:
        current = self._positions.get(transaction.ticker)
        if current is None:
            self._positions[transaction.ticker] = Position(
                transaction.ticker, transaction.quantity, transaction.price
            )
        else:
            self._positions[transaction.ticker] = current.after_buy(
                transaction.quantity, transaction.price
            )

    def _apply_sell(self, transaction: Transaction) -> None:
        current = self._positions.get(transaction.ticker)
        held = current.quantity if current else 0
        if transaction.quantity > held:
            raise ValueError(
                f"Cannot sell {transaction.quantity} {transaction.ticker} on "
                f"{transaction.trade_date}: only {held} held"
            )

        self._realized_gain += (
            transaction.price - current.average_cost
        ) * transaction.quantity

        if transaction.quantity == held:
            del self._positions[transaction.ticker]
        else:
            self._positions[transaction.ticker] = current.after_sell(
                transaction.quantity
            )
