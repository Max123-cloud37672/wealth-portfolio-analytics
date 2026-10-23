"""Tests for the Streamlit dashboard, run without a browser using AppTest.

The app reads the MySQL test database, freshly loaded with the sample data.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from wealth_analytics.database import Database
from wealth_analytics.repositories import ClientRepository, TransactionRepository
from wealth_analytics.sample_data import load_sample_data

DASHBOARD = Path(__file__).resolve().parents[1] / "app" / "dashboard.py"


@pytest.fixture
def app(database: Database, monkeypatch: pytest.MonkeyPatch) -> AppTest:
    """The dashboard as a fresh visitor sees it, reading the test database."""
    load_sample_data(database)
    monkeypatch.setenv("MYSQL_DATABASE", database.name)
    return AppTest.from_file(str(DASHBOARD), default_timeout=30).run()


def metric_value(app: AppTest, label: str) -> str:
    """The displayed value of the headline number with this label."""
    return next(metric.value for metric in app.metric if metric.label == label)


def test_dashboard_runs_without_errors(app: AppTest) -> None:
    assert not app.exception
    assert not app.error


def test_illustrative_data_notice_is_shown(app: AppTest) -> None:
    assert any("Illustrative data" in notice.value for notice in app.info)


def test_first_client_alphabetically_is_shown_by_default(app: AppTest) -> None:
    assert app.title[0].value == "Bouchard Estate"


def test_headline_numbers_use_cad_formatting(app: AppTest) -> None:
    assert metric_value(app, "Market value") == "$4,366,850"
    assert metric_value(app, "Net invested") == "$4,096,200"


def test_choosing_another_client_updates_the_page(app: AppTest) -> None:
    app.selectbox(key="client").select_index(3).run()

    assert app.title[0].value == "Tremblay Family Trust"
    assert metric_value(app, "Market value") == "$5,142,900"


def test_choosing_all_time_shows_the_return_since_the_first_trade(
    app: AppTest,
) -> None:
    app.segmented_control(key="period").set_value("All").run()

    assert metric_value(app, "Return (All)") == "+6.8%"
    assert metric_value(app, "Gain (All)") == "+$270,650"


def test_holdings_table_has_one_row_per_open_position(app: AppTest) -> None:
    assert len(app.dataframe[0].value) == 9


def test_trade_history_lists_every_trade(app: AppTest) -> None:
    assert len(app.dataframe[1].value) == 12


def test_recording_a_valid_trade_saves_it(app: AppTest, database: Database) -> None:
    app.number_input(key="trade_quantity").set_value(10).run()
    app.button[0].click().run()

    assert not app.error
    assert "Recorded: Buy 10" in app.success[0].value
    assert len(app.dataframe[1].value) == 13


def test_overselling_is_refused_and_nothing_is_saved(
    app: AppTest, database: Database
) -> None:
    app.selectbox(key="trade_ticker").set_value("TD").run()
    app.selectbox(key="trade_side").select_index(1).run()  # Sell
    app.number_input(key="trade_quantity").set_value(1_000_000).run()
    app.button[0].click().run()

    assert "Trade not recorded" in app.error[0].value
    client = ClientRepository(database).all()[0]
    assert len(TransactionRepository(database).for_client(client.client_id)) == 12
