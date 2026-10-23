"""Loading the fictional sample data from data/*.csv into MySQL.

Run from the project folder:  python -m wealth_analytics.sample_data [--reset]
"""

import argparse
import csv
from datetime import date
from pathlib import Path

from wealth_analytics.client import RiskProfile
from wealth_analytics.database import Database, DatabaseConfig
from wealth_analytics.repositories import (
    ClientRepository,
    PriceRepository,
    SecurityRepository,
    TransactionRepository,
)
from wealth_analytics.security import AssetType, Security
from wealth_analytics.transaction import Side, Transaction

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def read_clients(path: Path) -> list[tuple[str, RiskProfile]]:
    """Each client's name and risk profile, in file order."""
    with path.open(newline="") as file:
        return [(row["name"], RiskProfile(row["risk"])) for row in csv.DictReader(file)]


def read_transactions(path: Path) -> list[tuple[str, Transaction]]:
    """Each trade paired with the name of the client who made it."""
    with path.open(newline="") as file:
        return [
            (
                row["client"],
                Transaction(
                    trade_date=date.fromisoformat(row["trade_date"]),
                    ticker=row["ticker"],
                    side=Side(row["side"]),
                    quantity=float(row["quantity"]),
                    price=float(row["price"]),
                ),
            )
            for row in csv.DictReader(file)
        ]


def read_securities(path: Path) -> list[Security]:
    """Each security's reference details, in file order."""
    with path.open(newline="") as file:
        return [
            Security(
                ticker=row["ticker"],
                name=row["name"],
                asset_type=AssetType(row["asset_type"]),
                sector=row["sector"],
            )
            for row in csv.DictReader(file)
        ]


def read_prices(path: Path) -> list[tuple[str, date, float]]:
    """Each (ticker, date, closing price) row, in file order."""
    with path.open(newline="") as file:
        return [
            (row["ticker"], date.fromisoformat(row["price_date"]), float(row["close"]))
            for row in csv.DictReader(file)
        ]


def load_sample_data(
    database: Database, data_dir: Path = DATA_DIR, reset: bool = False
) -> None:
    """Create the tables if needed and fill them with the sample data.

    Refuses to load on top of existing clients unless reset=True, which first
    deletes every existing row.
    """
    database.create()
    clients = ClientRepository(database)
    if reset:
        database.delete_all_rows()
    elif clients.all():
        raise RuntimeError(
            "The database already has clients. Run again with --reset to replace them."
        )

    securities = SecurityRepository(database)
    for security in read_securities(data_dir / "securities.csv"):
        securities.add(security)
    PriceRepository(database).add_many(read_prices(data_dir / "prices.csv"))

    client_ids = {
        name: clients.add(name, risk).client_id
        for name, risk in read_clients(data_dir / "clients.csv")
    }
    transactions = TransactionRepository(database)
    for client_name, transaction in read_transactions(data_dir / "transactions.csv"):
        transactions.add(client_ids[client_name], transaction)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load the sample data into MySQL.")
    parser.add_argument(
        "--reset", action="store_true", help="delete existing data first"
    )
    args = parser.parse_args()

    config = DatabaseConfig.from_env()
    load_sample_data(Database(config), reset=args.reset)
    print(f"Sample data loaded into the '{config.database}' database.")


if __name__ == "__main__":
    main()
