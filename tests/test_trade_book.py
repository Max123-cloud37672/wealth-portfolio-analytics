"""Tests for TradeBook: recording new trades only when they keep the portfolio valid."""

from datetime import date

import pytest

from wealth_analytics.client import Client, RiskProfile
from wealth_analytics.database import Database
from wealth_analytics.repositories import (
    ClientRepository,
    SecurityRepository,
    TransactionRepository,
)
from wealth_analytics.security import AssetType, Security
from wealth_analytics.trade_book import TradeBook
from wealth_analytics.transaction import Side, Transaction


@pytest.fixture
def client(database: Database) -> Client:
    """A client who bought 100 RY on 2 March 2026."""
    SecurityRepository(database).add(
        Security("RY", "Royal Bank of Canada", AssetType.STOCK, "Financials")
    )
    client = ClientRepository(database).add("Tremblay Family Trust", RiskProfile.GROWTH)
    TransactionRepository(database).add(
        client.client_id, Transaction(date(2026, 3, 2), "RY", Side.BUY, 100, 150.00)
    )
    return client


def test_a_valid_trade_is_saved(database: Database, client: Client) -> None:
    trade = Transaction(date(2026, 3, 9), "RY", Side.SELL, 40, 155.00)

    TradeBook(database).record(client.client_id, trade)

    assert TransactionRepository(database).for_client(client.client_id)[-1] == trade


def test_selling_more_than_is_held_is_refused(
    database: Database, client: Client
) -> None:
    trade = Transaction(date(2026, 3, 9), "RY", Side.SELL, 101, 155.00)

    with pytest.raises(ValueError, match="only 100"):
        TradeBook(database).record(client.client_id, trade)

    assert len(TransactionRepository(database).for_client(client.client_id)) == 1


def test_selling_before_the_shares_were_bought_is_refused(
    database: Database, client: Client
) -> None:
    trade = Transaction(date(2026, 3, 1), "RY", Side.SELL, 10, 149.00)

    with pytest.raises(ValueError):
        TradeBook(database).record(client.client_id, trade)


def test_an_unknown_ticker_is_refused(database: Database, client: Client) -> None:
    trade = Transaction(date(2026, 3, 9), "ZZZ", Side.BUY, 10, 5.00)

    with pytest.raises(ValueError, match="ZZZ"):
        TradeBook(database).record(client.client_id, trade)
