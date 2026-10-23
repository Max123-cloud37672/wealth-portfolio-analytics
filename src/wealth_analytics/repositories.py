"""Saving the project's data to MySQL and loading it back as Python objects.

These classes are the only place that writes SQL, so the rest of the project
works with Client, Transaction and Security objects and never needs to know
about tables.
Values are always passed as %s parameters, never pasted into the SQL text,
which protects against SQL injection.
"""

from collections.abc import Iterable
from datetime import date

import mysql.connector
from mysql.connector import errorcode

from wealth_analytics.client import Client, RiskProfile
from wealth_analytics.database import Database
from wealth_analytics.security import AssetType, Security
from wealth_analytics.transaction import Side, Transaction


class ClientRepository:
    """Reads and writes rows in the clients table."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def add(self, name: str, risk: RiskProfile) -> Client:
        """Save a new client and return it with its database ID."""
        with self._database.connect() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO clients (name, risk) VALUES (%s, %s)",
                    (name, risk.value),
                )
            except mysql.connector.IntegrityError as error:
                if error.errno == errorcode.ER_DUP_ENTRY:
                    raise ValueError(
                        f"A client named {name!r} already exists"
                    ) from None
                raise
            connection.commit()
            return Client(cursor.lastrowid, name, risk)

    def all(self) -> list[Client]:
        """Every client, in alphabetical order."""
        with self._database.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT client_id, name, risk FROM clients ORDER BY name")
            return [
                Client(client_id, name, RiskProfile(risk))
                for client_id, name, risk in cursor.fetchall()
            ]


class TransactionRepository:
    """Reads and writes rows in the transactions table."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def add(self, client_id: int, transaction: Transaction) -> None:
        """Save one trade for the given client."""
        with self._database.connect() as connection:
            connection.cursor().execute(
                "INSERT INTO transactions "
                "(client_id, trade_date, ticker, side, quantity, price) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    client_id,
                    transaction.trade_date,
                    transaction.ticker,
                    transaction.side.value,
                    transaction.quantity,
                    transaction.price,
                ),
            )
            connection.commit()

    def for_client(self, client_id: int) -> list[Transaction]:
        """The client's trades, oldest first (same-day trades in the order saved)."""
        with self._database.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT trade_date, ticker, side, quantity, price FROM transactions "
                "WHERE client_id = %s ORDER BY trade_date, transaction_id",
                (client_id,),
            )
            # MySQL returns DECIMAL columns as Decimal; convert to float to match
            # the rest of the project.
            return [
                Transaction(
                    trade_date, ticker, Side(side), float(quantity), float(price)
                )
                for trade_date, ticker, side, quantity, price in cursor.fetchall()
            ]


class SecurityRepository:
    """Reads and writes rows in the securities table."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def add(self, security: Security) -> None:
        """Save one security's reference details."""
        with self._database.connect() as connection:
            connection.cursor().execute(
                "INSERT INTO securities (ticker, name, asset_type, sector) "
                "VALUES (%s, %s, %s, %s)",
                (
                    security.ticker,
                    security.name,
                    security.asset_type.value,
                    security.sector,
                ),
            )
            connection.commit()

    def all(self) -> list[Security]:
        """Every security, in ticker order."""
        with self._database.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT ticker, name, asset_type, sector FROM securities "
                "ORDER BY ticker"
            )
            return [
                Security(ticker, name, AssetType(asset_type), sector)
                for ticker, name, asset_type, sector in cursor.fetchall()
            ]


class PriceRepository:
    """Reads and writes rows in the prices table (one closing price per day)."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def add_many(self, prices: Iterable[tuple[str, date, float]]) -> None:
        """Save (ticker, date, close) rows in one go. Each ticker must be a security."""
        with self._database.connect() as connection:
            try:
                connection.cursor().executemany(
                    "INSERT INTO prices (ticker, price_date, close) "
                    "VALUES (%s, %s, %s)",
                    list(prices),
                )
            except mysql.connector.IntegrityError as error:
                if error.errno == errorcode.ER_NO_REFERENCED_ROW_2:
                    raise ValueError(
                        "Prices can only be saved for tickers in the securities table"
                    ) from None
                raise
            connection.commit()

    def closes(self, ticker: str) -> dict[date, float]:
        """The ticker's closing price on each day, oldest first."""
        with self._database.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT price_date, close FROM prices WHERE ticker = %s "
                "ORDER BY price_date",
                (ticker,),
            )
            return {price_date: float(close) for price_date, close in cursor.fetchall()}
