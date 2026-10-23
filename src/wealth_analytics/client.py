"""A fictional high-net-worth client whose portfolio is tracked."""

from dataclasses import dataclass
from enum import Enum

from wealth_analytics.validation import require_text


class RiskProfile(Enum):
    """How much investment risk the client is comfortable with."""

    CONSERVATIVE = "Conservative"
    BALANCED = "Balanced"
    GROWTH = "Growth"


@dataclass(frozen=True)
class Client:
    """One client, e.g. the Tremblay Family Trust with a Balanced risk profile."""

    client_id: int
    name: str
    risk: RiskProfile

    def __post_init__(self) -> None:
        """Reject invalid inputs as soon as a client is created."""
        require_text("name", self.name)
        if not isinstance(self.risk, RiskProfile):
            raise TypeError(
                f"risk must be a RiskProfile (e.g. RiskProfile.GROWTH), "
                f"got {self.risk!r}"
            )
