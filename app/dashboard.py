"""Streamlit dashboard for the illustrative HNW portfolio analytics project.

Run it from the project folder with:  streamlit run app/dashboard.py

This file only displays results and collects input. Every calculation lives in
the wealth_analytics package, and all data is read from (and new trades are
saved to) the local MySQL database set up in .env.
"""

from datetime import date
from typing import NamedTuple

import mysql.connector
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from wealth_analytics.client import Client
from wealth_analytics.database import Database, DatabaseConfig
from wealth_analytics.performance import Performance
from wealth_analytics.portfolio import Portfolio
from wealth_analytics.price_history import PriceHistory
from wealth_analytics.reporting import (
    Period,
    Summary,
    allocation,
    holdings_table,
    period_start,
    return_comparison,
    summarize,
    transactions_table,
    value_history,
)
from wealth_analytics.repositories import (
    ClientRepository,
    PriceRepository,
    SecurityRepository,
    TransactionRepository,
)
from wealth_analytics.security import Security
from wealth_analytics.trade_book import TradeBook
from wealth_analytics.transaction import Side, Transaction

BENCHMARK = "XIU"
BENCHMARK_NAME = "S&P/TSX 60 (XIU)"

# Chart colours: blue for the client, orange for the benchmark, and a muted grey
# for "net invested", which is a reference line rather than a result.
PORTFOLIO_COLOUR = "#2a78d6"
BENCHMARK_COLOUR = "#eb6834"
REFERENCE_COLOUR = "#898781"

ILLUSTRATIVE_NOTICE = (
    "**Illustrative data.** All clients are fictional and all prices are simulated. "
    "Nothing shown is real client information, market data or performance."
)


# --- Number formatting ------------------------------------------------------


def format_cad(amount: float) -> str:
    """Format a dollar amount, e.g. 2797400 -> '$2,797,400'."""
    return f"${amount:,.0f}"


def format_signed_cad(amount: float) -> str:
    """Format a gain or loss with its sign, e.g. 931850 -> '+$931,850'."""
    sign = "+" if amount >= 0 else "-"
    return f"{sign}${abs(amount):,.0f}"


def format_signed_pct(fraction: float) -> str:
    """Format a fraction as a signed percentage, e.g. 0.333 -> '+33.3%'."""
    return f"{fraction:+.1%}"


# --- Data -------------------------------------------------------------------


@st.cache_resource
def get_database() -> Database:
    """The MySQL database from .env, shared by every page view."""
    return Database(DatabaseConfig.from_env())


@st.cache_data
def load_market_data() -> tuple[PriceHistory, dict[str, Security]]:
    """Prices and security details. They never change while the app runs."""
    database = get_database()
    securities = {s.ticker: s for s in SecurityRepository(database).all()}
    return PriceRepository(database).history(), securities


# --- Page sections ----------------------------------------------------------


def show_sidebar(clients: list[Client]) -> tuple[Client, Period]:
    """Client and period pickers."""
    with st.sidebar:
        st.header("Wealth Portfolio Analytics")
        client = st.selectbox(
            "Client", clients, format_func=lambda c: c.name, key="client"
        )
        st.caption(f"Risk profile: **{client.risk.value}**")
        period = st.segmented_control(
            "Period",
            list(Period),
            format_func=lambda p: p.value,
            default=Period.ONE_YEAR,
            key="period",
        )
        st.caption(f"All amounts in CAD. Benchmark: {BENCHMARK_NAME}.")
    return client, period or Period.ONE_YEAR


def show_headline_numbers(summary: Summary, period: Period) -> None:
    """Four headline figures across the top of the page."""
    value, invested, gain, twr = st.columns(4)
    value.metric("Market value", format_cad(summary.market_value))
    invested.metric(
        "Net invested",
        format_cad(summary.net_invested),
        help="Money put in by purchases minus money taken out by sales.",
    )
    gain.metric(f"Gain ({period.value})", format_signed_cad(summary.gain))
    excess = summary.period_return - summary.benchmark_return
    twr.metric(
        f"Return ({period.value})",
        format_signed_pct(summary.period_return),
        delta=f"{excess * 100:+.1f} pts vs TSX 60",
        help=(
            "Time-weighted return: how the investments performed, "
            "ignoring when money was added or withdrawn."
        ),
    )


class Line(NamedTuple):
    """One series on a line chart."""

    name: str
    values: pd.Series
    colour: str
    steps: bool = False  # jump on the day it changes, instead of sloping


def line_chart(
    dates: pd.Series,
    lines: list[Line],
    hover_format: str,
    tick_format: str,
    y_title: str,
) -> go.Figure:
    """Thin lines on one shared axis, with one tooltip listing every series."""
    figure = go.Figure()
    for line in lines:
        figure.add_trace(
            go.Scatter(
                x=dates,
                y=line.values,
                name=line.name,
                mode="lines",
                line={
                    "color": line.colour,
                    "width": 2,
                    "shape": "hv" if line.steps else "linear",
                },
                hovertemplate=f"%{{y:{hover_format}}}<extra>{line.name}</extra>",
            )
        )
    figure.update_layout(
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.08, "x": 0},
        yaxis={"title": y_title, "tickformat": tick_format},
        margin={"l": 0, "r": 10, "t": 30, "b": 0},
        height=360,
    )
    return figure


def show_performance(
    performance: Performance, prices: PriceHistory, start: date | None
) -> None:
    """Value over time, and returns compared with the benchmark."""
    history = value_history(performance, start)
    st.subheader("Market value and money invested")
    value_chart = line_chart(
        history["Date"],
        [
            Line("Market value", history["Market value"], PORTFOLIO_COLOUR),
            Line("Net invested", history["Net invested"], REFERENCE_COLOUR, steps=True),
        ],
        hover_format="$,.0f",
        tick_format="$,.0f",
        y_title="CAD",
    )
    st.plotly_chart(value_chart, width="stretch")

    comparison = return_comparison(performance, prices, start, BENCHMARK)
    st.subheader(f"Return compared with the {BENCHMARK_NAME}")
    return_chart = line_chart(
        comparison["Date"],
        [
            Line(
                "Portfolio (time-weighted)", comparison["Portfolio"], PORTFOLIO_COLOUR
            ),
            Line(BENCHMARK_NAME, comparison["Benchmark"], BENCHMARK_COLOUR),
        ],
        hover_format="+.1%",
        tick_format=".0%",
        y_title="Return since start of period",
    )
    return_chart.add_hline(y=0, line_width=1, line_color=REFERENCE_COLOUR)
    st.plotly_chart(return_chart, width="stretch")


def allocation_chart(weights: pd.Series, category: str) -> go.Figure:
    """Horizontal bars of portfolio share, largest at the top."""
    figure = go.Figure(
        go.Bar(
            x=list(weights.values),
            y=list(weights.index),
            orientation="h",
            marker={"color": PORTFOLIO_COLOUR, "cornerradius": 4},
            text=[f"{share:.1%}" for share in weights.values],
            textposition="outside",
            cliponaxis=False,
            hovertemplate=f"{category}: %{{y}}<br>Share: %{{x:.1%}}<extra></extra>",
        )
    )
    figure.update_layout(
        xaxis={
            "title": "Share of market value",
            "tickformat": ".0%",
            "range": [0, max(weights.values) * 1.18],
        },
        yaxis={"autorange": "reversed"},
        height=120 + 36 * len(weights),
        margin={"l": 0, "r": 40, "t": 10, "b": 0},
        bargap=0.35,
        showlegend=False,
    )
    return figure


def show_holdings(
    portfolio: Portfolio,
    securities: dict[str, Security],
    prices: PriceHistory,
    day: date,
) -> None:
    """Allocation chart and a table of every open position."""
    if not portfolio.positions:
        st.info("This client has no open positions.")
        return

    table = holdings_table(portfolio, securities, prices, day)
    st.subheader("Allocation")
    group_by = st.segmented_control(
        "Group by", ["Sector", "Asset type", "Ticker"], default="Sector", key="group_by"
    )
    group_by = group_by or "Sector"
    st.plotly_chart(
        allocation_chart(allocation(table, by=group_by), group_by), width="stretch"
    )

    st.subheader(f"Holdings at the close on {day:%d %b %Y}")
    table[["Gain %", "Weight"]] *= 100  # fractions -> percentages for display
    number = st.column_config.NumberColumn
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_order=[
            "Ticker",
            "Name",
            "Sector",
            "Quantity",
            "Average cost",
            "Price",
            "Cost basis",
            "Market value",
            "Weight",
            "Gain",
            "Gain %",
        ],
        column_config={
            "Quantity": number("Qty", format="localized"),
            "Average cost": number("Avg cost", format="dollar"),
            "Price": number("Price", format="dollar"),
            "Cost basis": number("Invested", format="$%,.0f"),
            "Market value": number("Value", format="$%,.0f"),
            "Gain": number("Gain ($)", format="%+,.0f"),
            "Gain %": number("Gain", format="%+.1f%%"),
            "Weight": number("Weight", format="%.1f%%"),
        },
    )


def show_trades(trades: list[Transaction]) -> None:
    """The trade history, filterable by ticker and side."""
    st.subheader("Trade history")
    table = transactions_table(trades)
    tickers_filter, side_filter = st.columns([3, 1])
    tickers = tickers_filter.multiselect(
        "Tickers", sorted(table["Ticker"].unique()), placeholder="All tickers"
    )
    sides = side_filter.pills(
        "Side", [side.value for side in Side], selection_mode="multi", key="sides"
    )
    if tickers:
        table = table[table["Ticker"].isin(tickers)]
    if sides:
        table = table[table["Side"].isin(sides)]

    number = st.column_config.NumberColumn
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
            "Quantity": number("Qty", format="localized"),
            "Price": number("Price", format="dollar"),
            "Amount": number("Amount", format="$%,.0f"),
        },
    )


def show_trade_entry(
    client: Client, securities: dict[str, Security], prices: PriceHistory
) -> None:
    """A small form that saves a new trade to MySQL after checking the rules."""
    st.subheader("Record a trade")
    trading_days = prices.trading_days()
    ticker_col, side_col, date_col, quantity_col, price_col = st.columns(5)
    ticker = ticker_col.selectbox("Ticker", sorted(securities), key="trade_ticker")
    side = side_col.selectbox(
        "Side", list(Side), format_func=lambda s: s.value, key="trade_side"
    )
    day = date_col.date_input(
        "Trade date",
        value=trading_days[-1],
        min_value=trading_days[0],
        max_value=trading_days[-1],
        key="trade_date",
    )
    quantity = quantity_col.number_input(
        "Quantity", min_value=1, value=100, step=1, key="trade_quantity"
    )
    price = price_col.number_input(
        "Price",
        min_value=0.01,
        value=prices.close_on(ticker, day),
        format="%.2f",
        help="Defaults to that day's closing price.",
        key=f"trade_price_{ticker}_{day}",
    )

    if st.button("Record trade", type="primary"):
        trade = Transaction(day, ticker, side, float(quantity), float(price))
        try:
            TradeBook(get_database()).record(client.client_id, trade)
        except ValueError as error:
            st.error(f"Trade not recorded: {error}")
        else:
            st.session_state["flash"] = (
                f"Recorded: {side.value} {quantity:,} {ticker} at ${price:,.2f} "
                f"on {day:%d %b %Y}."
            )
            st.rerun()


# --- Page -------------------------------------------------------------------


def main() -> None:
    st.set_page_config(page_title="Wealth Portfolio Analytics", layout="wide")

    try:
        database = get_database()
        prices, securities = load_market_data()
        clients = ClientRepository(database).all()
    except (RuntimeError, mysql.connector.Error) as error:
        st.error(
            f"Could not read the database: {error}\n\n"
            "Check that MySQL is running and .env is filled in, then load the "
            "sample data with `python -m wealth_analytics.sample_data`."
        )
        st.stop()
    if not clients:
        st.warning(
            "The database has no clients yet. Load the sample data with "
            "`python -m wealth_analytics.sample_data`."
        )
        st.stop()

    client, period = show_sidebar(clients)
    trades = TransactionRepository(database).for_client(client.client_id)

    st.title(client.name)
    st.info(ILLUSTRATIVE_NOTICE)
    if flash := st.session_state.pop("flash", None):
        st.success(flash)

    performance_tab, holdings_tab, trades_tab = st.tabs(
        ["Performance", "Holdings", "Trades"]
    )
    performance = Performance(trades, prices)
    if performance.daily_values:
        last_day = performance.daily_values[-1].day
        start = period_start(period, last_day)
        if start is not None and start < performance.daily_values[0].day:
            start = None  # the period reaches back before the first trade

        with performance_tab:
            show_headline_numbers(
                summarize(performance, prices, start, BENCHMARK), period
            )
            show_performance(performance, prices, start)
        with holdings_tab:
            show_holdings(Portfolio(trades), securities, prices, last_day)
    else:
        performance_tab.info("No trades yet: record one in the Trades tab.")

    with trades_tab:
        if trades:
            show_trades(trades)
        show_trade_entry(client, securities, prices)


main()
