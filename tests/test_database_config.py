"""Tests for DatabaseConfig: reading MySQL login details from settings."""

import pytest

from wealth_analytics.database import DatabaseConfig

SETTINGS = {
    "MYSQL_HOST": "localhost",
    "MYSQL_PORT": "3306",
    "MYSQL_USER": "analyst",
    "MYSQL_PASSWORD": "secret-value",
    "MYSQL_DATABASE": "wealth_analytics",
}


def test_settings_are_read_into_a_config() -> None:
    config = DatabaseConfig.from_env(SETTINGS)

    assert config.host == "localhost"
    assert config.port == 3306
    assert config.user == "analyst"
    assert config.database == "wealth_analytics"


def test_a_missing_setting_gives_a_clear_error() -> None:
    settings = {key: value for key, value in SETTINGS.items() if key != "MYSQL_USER"}

    with pytest.raises(RuntimeError, match="MYSQL_USER"):
        DatabaseConfig.from_env(settings)


def test_password_is_hidden_when_the_config_is_printed() -> None:
    config = DatabaseConfig.from_env(SETTINGS)

    assert "secret-value" not in repr(config)


@pytest.mark.parametrize("bad_name", ["", "wealth-analytics", "x; DROP TABLE clients"])
def test_database_name_must_be_letters_digits_or_underscores(bad_name: str) -> None:
    with pytest.raises(ValueError):
        DatabaseConfig.from_env({**SETTINGS, "MYSQL_DATABASE": bad_name})
