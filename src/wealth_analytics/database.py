"""Connecting to the local MySQL server using the login details in .env."""

import os
import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field

import mysql.connector
from dotenv import find_dotenv, load_dotenv
from mysql.connector.abstracts import MySQLConnectionAbstract

from wealth_analytics.schema import TABLES

_SAFE_NAME = re.compile(r"\w+", re.ASCII)


@dataclass(frozen=True)
class DatabaseConfig:
    """Where the MySQL server is and how to log in. The password is never printed."""

    host: str
    port: int
    user: str
    password: str = field(repr=False)
    database: str

    def __post_init__(self) -> None:
        # The name is placed directly into CREATE DATABASE, so only allow a
        # plain identifier (letters, digits, underscores) to rule out injection.
        if not _SAFE_NAME.fullmatch(self.database):
            raise ValueError(
                f"database name must be letters, digits or underscores, "
                f"got {self.database!r}"
            )

    @classmethod
    def from_env(cls, settings: Mapping[str, str] | None = None) -> DatabaseConfig:
        """Read the MYSQL_* settings, from .env and the environment by default."""
        if settings is None:
            load_dotenv(find_dotenv(usecwd=True))
            settings = os.environ
        try:
            return cls(
                host=settings["MYSQL_HOST"],
                port=int(settings["MYSQL_PORT"]),
                user=settings["MYSQL_USER"],
                password=settings["MYSQL_PASSWORD"],
                database=settings["MYSQL_DATABASE"],
            )
        except KeyError as missing:
            raise RuntimeError(
                f"Missing setting {missing}: copy .env.example to .env and fill it in"
            ) from None


class Database:
    """The project's MySQL database: creates it if needed and hands out connections."""

    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config

    @contextmanager
    def connect(self) -> Iterator[MySQLConnectionAbstract]:
        """A connection to this database, closed automatically afterwards."""
        connection = self._open(database=self._config.database)
        try:
            yield connection
        finally:
            connection.close()

    def create(self) -> None:
        """Create the database and its tables if they don't exist yet."""
        server = self._open(database=None)
        try:
            server.cursor().execute(
                f"CREATE DATABASE IF NOT EXISTS `{self._config.database}`"
            )
        finally:
            server.close()

        with self.connect() as connection:
            cursor = connection.cursor()
            for statement in TABLES:
                cursor.execute(statement)
            connection.commit()

    def delete_all_rows(self) -> None:
        """Empty every table (trades first, as they refer to clients)."""
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM transactions")
            cursor.execute("DELETE FROM clients")
            connection.commit()

    def _open(self, database: str | None) -> MySQLConnectionAbstract:
        return mysql.connector.connect(
            host=self._config.host,
            port=self._config.port,
            user=self._config.user,
            password=self._config.password,
            database=database,
        )
