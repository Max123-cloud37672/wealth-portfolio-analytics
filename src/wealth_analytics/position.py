"""How many shares of one ticker a client holds, and what they paid on average."""

from dataclasses import dataclass

from wealth_analytics.validation import require_positive_number, require_text


@dataclass(frozen=True)
class Position:
    """One holding, e.g. 150 shares of RY at an average cost of $15.

    All amounts are in Canadian dollars (CAD). Prices are per share.
    """

    ticker: str
    quantity: float
    average_cost: float

    def __post_init__(self) -> None:
        """Reject invalid inputs as soon as a position is created."""
        require_text("ticker", self.ticker)
        for field_name in ("quantity", "average_cost"):
            require_positive_number(field_name, getattr(self, field_name))

    @property
    def cost_basis(self) -> float:
        """Total amount invested: quantity x average cost."""
        return self.quantity * self.average_cost

    def after_buy(self, quantity: float, price: float) -> Position:
        """The position after buying more shares: the average cost is re-weighted."""
        new_quantity = self.quantity + quantity
        new_cost_basis = self.cost_basis + quantity * price
        return Position(self.ticker, new_quantity, new_cost_basis / new_quantity)

    def after_sell(self, quantity: float) -> Position:
        """The position after selling some shares: the average cost is unchanged."""
        return Position(self.ticker, self.quantity - quantity, self.average_cost)
