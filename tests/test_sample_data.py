"""Tests for the sample data: reading the CSV files and loading them into MySQL."""

from datetime import date
from pathlib import Path

import pytest

from wealth_analytics.client import RiskProfile
from wealth_analytics.database import Database
from wealth_analytics.portfolio import Portfolio
from wealth_analytics.repositories import ClientRepository, TransactionRepository
from wealth_analytics.sample_data import (
    DATA_DIR,
    load_sample_data,
    read_clients,
    read_transactions,
)
from wealth_analytics.transaction import Side, Transaction


def write_csv(path: Path, text: str) -> Path:
    path.write_text(text)
    return path


# --- Reading the CSV files --------------------------------------------------


def test_clients_are_read_with_their_risk_profile(tmp_path: Path) -> None:
    path = write_csv(tmp_path / "clients.csv", "name,risk\nBouchard Estate,Balanced\n")

    assert read_clients(path) == [("Bouchard Estate", RiskProfile.BALANCED)]


def test_transactions_are_read_with_their_client(tmp_path: Path) -> None:
    path = write_csv(
        tmp_path / "transactions.csv",
        "client,trade_date,ticker,side,quantity,price\n"
        "Bouchard Estate,2025-01-20,TD,Buy,6000,79.40\n",
    )

    assert read_transactions(path) == [
        (
            "Bouchard Estate",
            Transaction(date(2025, 1, 20), "TD", Side.BUY, 6000, 79.40),
        )
    ]


def test_an_unknown_side_is_rejected(tmp_path: Path) -> None:
    path = write_csv(
        tmp_path / "transactions.csv",
        "client,trade_date,ticker,side,quantity,price\n"
        "Bouchard Estate,2025-01-20,TD,Hold,6000,79.40\n",
    )

    with pytest.raises(ValueError):
        read_transactions(path)


# --- The project's own sample files -----------------------------------------


def test_every_trade_belongs_to_a_known_client() -> None:
    client_names = {name for name, _ in read_clients(DATA_DIR / "clients.csv")}
    trades = read_transactions(DATA_DIR / "transactions.csv")

    assert {client for client, _ in trades} <= client_names


def test_every_clients_trades_replay_without_overselling() -> None:
    trades = read_transactions(DATA_DIR / "transactions.csv")

    for client in {client for client, _ in trades}:
        Portfolio([trade for name, trade in trades if name == client])


# --- Loading into MySQL -----------------------------------------------------


def test_sample_data_loads_every_client_and_trade(database: Database) -> None:
    load_sample_data(database)

    clients = ClientRepository(database).all()
    transactions = TransactionRepository(database)
    loaded = sum(len(transactions.for_client(c.client_id)) for c in clients)
    assert len(clients) == len(read_clients(DATA_DIR / "clients.csv"))
    assert loaded == len(read_transactions(DATA_DIR / "transactions.csv"))


def test_loading_twice_is_refused_unless_reset(database: Database) -> None:
    load_sample_data(database)

    with pytest.raises(RuntimeError, match="--reset"):
        load_sample_data(database)

    load_sample_data(database, reset=True)
    assert len(ClientRepository(database).all()) == 4
