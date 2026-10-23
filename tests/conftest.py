"""Shared fixtures: a separate MySQL test database, emptied before each test."""

import os
from collections.abc import Iterator
from dataclasses import replace

import mysql.connector
import pytest

from wealth_analytics.database import Database, DatabaseConfig


@pytest.fixture(scope="session")
def test_database() -> Database:
    """The test database, created once per test run (never the real one)."""
    try:
        config = DatabaseConfig.from_env()
    except RuntimeError as error:
        pytest.skip(f"MySQL settings not found: {error}")

    test_name = os.environ.get("MYSQL_TEST_DATABASE", "wealth_analytics_test")
    if test_name == config.database:
        pytest.exit("Refusing to run: the test database is the real database")
    database = Database(replace(config, database=test_name))
    try:
        database.create()
    except mysql.connector.Error as error:
        pytest.skip(f"MySQL is not reachable: {error.msg}")
    return database


@pytest.fixture
def database(test_database: Database) -> Iterator[Database]:
    """The test database with every table emptied, so each test starts clean."""
    test_database.delete_all_rows()
    yield test_database
