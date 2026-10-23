"""Tests for the repositories: saving to and loading from the MySQL test database."""

from datetime import date

import pytest

from wealth_analytics.client import RiskProfile
from wealth_analytics.database import Database
from wealth_analytics.repositories import ClientRepository, TransactionRepository
from wealth_analytics.transaction import Side, Transaction


def test_an_added_client_can_be_listed(database: Database) -> None:
    clients = ClientRepository(database)

    added = clients.add("Tremblay Family Trust", RiskProfile.BALANCED)

    assert clients.all() == [added]
    assert added.client_id is not None


def test_clients_are_listed_by_name(database: Database) -> None:
    clients = ClientRepository(database)
    clients.add("Zhang Holdings", RiskProfile.GROWTH)
    clients.add("Bouchard Estate", RiskProfile.CONSERVATIVE)

    assert [client.name for client in clients.all()] == [
        "Bouchard Estate",
        "Zhang Holdings",
    ]


def test_saved_transactions_load_back_unchanged(database: Database) -> None:
    client = ClientRepository(database).add("Tremblay Family Trust", RiskProfile.GROWTH)
    transactions = TransactionRepository(database)
    trade = Transaction(date(2026, 3, 2), "RY", Side.BUY, 200, 150.25)

    transactions.add(client.client_id, trade)

    assert transactions.for_client(client.client_id) == [trade]


def test_transactions_load_oldest_first(database: Database) -> None:
    client = ClientRepository(database).add("Tremblay Family Trust", RiskProfile.GROWTH)
    transactions = TransactionRepository(database)
    later = Transaction(date(2026, 5, 1), "RY", Side.SELL, 50, 160.00)
    earlier = Transaction(date(2026, 3, 2), "RY", Side.BUY, 200, 150.00)

    transactions.add(client.client_id, later)
    transactions.add(client.client_id, earlier)

    assert transactions.for_client(client.client_id) == [earlier, later]


def test_each_client_only_sees_their_own_transactions(database: Database) -> None:
    clients = ClientRepository(database)
    first = clients.add("Tremblay Family Trust", RiskProfile.GROWTH)
    second = clients.add("Bouchard Estate", RiskProfile.CONSERVATIVE)
    transactions = TransactionRepository(database)
    trade = Transaction(date(2026, 3, 2), "RY", Side.BUY, 200, 150.00)

    transactions.add(first.client_id, trade)

    assert transactions.for_client(second.client_id) == []


def test_two_clients_cannot_share_a_name(database: Database) -> None:
    clients = ClientRepository(database)
    clients.add("Tremblay Family Trust", RiskProfile.GROWTH)

    with pytest.raises(ValueError):
        clients.add("Tremblay Family Trust", RiskProfile.BALANCED)
