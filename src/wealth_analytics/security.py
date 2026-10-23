"""Reference details for one investment: its name, type and sector."""

from dataclasses import dataclass
from enum import Enum

from wealth_analytics.validation import require_text


class AssetType(Enum):
    """The kinds of investment the project supports."""

    STOCK = "Stock"
    ETF = "ETF"


@dataclass(frozen=True)
class Security:
    """One listed investment, e.g. RY: Royal Bank of Canada, a Financials stock."""

    ticker: str
    name: str
    asset_type: AssetType
    sector: str

    def __post_init__(self) -> None:
        """Reject invalid inputs as soon as a security is created."""
        for field_name in ("ticker", "name", "sector"):
            require_text(field_name, getattr(self, field_name))

        if not isinstance(self.asset_type, AssetType):
            raise TypeError(
                f"asset_type must be an AssetType (e.g. AssetType.STOCK), "
                f"got {self.asset_type!r}"
            )
