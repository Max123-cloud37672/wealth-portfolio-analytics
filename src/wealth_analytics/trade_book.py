"""Recording a new trade, but only if the client's history still makes sense."""

from wealth_analytics.database import Database
from wealth_analytics.portfolio import Portfolio
from wealth_analytics.repositories import SecurityRepository, TransactionRepository
from wealth_analytics.transaction import Transaction


class TradeBook:
    """Checks a new trade against the rules before saving it to MySQL."""

    def __init__(self, database: Database) -> None:
        self._securities = SecurityRepository(database)
        self._transactions = TransactionRepository(database)

    def record(self, client_id: int, trade: Transaction) -> None:
        """Save the trade, or raise ValueError (and save nothing) if it breaks a rule.

        The ticker must be a known security, and replaying the client's full
        history with the new trade must never sell shares that are not held,
        which also catches a back-dated sale that would break a later one.
        """
        known_tickers = {security.ticker for security in self._securities.all()}
        if trade.ticker not in known_tickers:
            raise ValueError(f"{trade.ticker} is not a known security")

        Portfolio([*self._transactions.for_client(client_id), trade])
        self._transactions.add(client_id, trade)
