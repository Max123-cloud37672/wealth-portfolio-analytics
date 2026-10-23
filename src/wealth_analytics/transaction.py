"""A single buy or sell trade in a client's account."""

from dataclasses import dataclass
from datetime import date
from enum import Enum

from wealth_analytics.validation import require_positive_number, require_text


class Side(Enum):
    """The direction of a trade."""

    BUY = "Buy"
    SELL = "Sell"


@dataclass(frozen=True)
class Transaction:
    """One trade, e.g. bought 200 shares of RY at $150 on 2 March 2026.

    All amounts are in Canadian dollars (CAD). Prices are per share.
    """

    trade_date: date
    ticker: str
    side: Side
    quantity: float
    price: float

    def __post_init__(self) -> None:
        """Reject invalid inputs as soon as a transaction is created."""
        if not isinstance(self.trade_date, date):
            raise TypeError(
                f"trade_date must be a date (e.g. date(2026, 3, 2)), "
                f"got {self.trade_date!r}"
            )

        require_text("ticker", self.ticker)

        if not isinstance(self.side, Side):
            raise TypeError(f"side must be a Side (e.g. Side.BUY), got {self.side!r}")

        for field_name in ("quantity", "price"):
            require_positive_number(field_name, getattr(self, field_name))

    @property
    def amount(self) -> float:
        """Total value of the trade: quantity x price."""
        return self.quantity * self.price

    @property
    def signed_quantity(self) -> float:
        """Shares added to the position: positive for a buy, negative for a sell."""
        if self.side is Side.SELL:
            return -self.quantity
        return self.quantity
