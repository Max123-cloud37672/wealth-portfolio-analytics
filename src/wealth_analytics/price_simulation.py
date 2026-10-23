"""Made-up daily closing prices for the sample data (illustrative, not market data).

Each ticker's price is pinned to a few known "anchor" prices: every sample trade
price, plus a chosen price on the last day. Between two anchors the price follows
a straight line (on a log scale) plus small random daily moves that are forced
back to zero at the next anchor, so every sample trade happened at that day's
close. In statistics this is called a Brownian bridge.

Regenerate data/prices.csv from the project folder with:
    python -m wealth_analytics.price_simulation
"""

import csv
import math
import random
from datetime import date, timedelta
from itertools import pairwise

from wealth_analytics.sample_data import DATA_DIR, read_transactions

FIRST_DAY = date(2025, 1, 2)
LAST_DAY = date(2026, 10, 23)
SEED = 2026

# Illustrative closing prices on LAST_DAY.
LAST_CLOSES = {
    "RY": 182.40, "TD": 96.15, "NA": 141.70, "BNS": 79.60, "SLF": 82.30,
    "BN": 88.50, "ENB": 63.20, "CNR": 152.30, "SHOP": 168.20, "CSU": 4210.00,
    "ATD": 76.40, "L": 192.80, "BCE": 33.90, "FTS": 66.75, "AEM": 162.50,
    "XIU": 41.85, "VFV": 158.60, "ZDV": 25.10, "XBB": 28.45,
}  # fmt: skip

# Typical size of one day's move (1.2% unless listed): bond ETFs move least,
# broad index ETFs less than single stocks, growth and gold stocks the most.
DEFAULT_DAILY_VOLATILITY = 0.012
DAILY_VOLATILITY = {
    "XBB": 0.003, "ZDV": 0.006, "XIU": 0.007, "VFV": 0.008,
    "CSU": 0.016, "AEM": 0.020, "SHOP": 0.025,
}  # fmt: skip


def weekdays_between(first: date, last: date) -> list[date]:
    """Every Monday to Friday from first to last, inclusive (holidays ignored)."""
    days = (first + timedelta(days=offset) for offset in range((last - first).days + 1))
    return [day for day in days if day.weekday() < 5]


def simulate_closes(
    days: list[date],
    anchors: dict[date, float],
    daily_volatility: float,
    rng: random.Random,
) -> dict[date, float]:
    """A closing price for every day, passing exactly through each anchor price."""
    position = {day: index for index, day in enumerate(days)}
    if days[0] not in anchors or days[-1] not in anchors:
        raise ValueError("The first and last day must both have an anchor price")
    off_days = sorted(day for day in anchors if day not in position)
    if off_days:
        raise ValueError(f"Anchor dates are not trading days: {off_days}")

    points = sorted((position[day], math.log(price)) for day, price in anchors.items())
    log_prices = [0.0] * len(days)
    for (start, start_log), (end, end_log) in pairwise(points):
        steps = end - start
        walk = [0.0]
        for _ in range(steps):
            walk.append(walk[-1] + rng.gauss(0, daily_volatility))
        for step in range(steps + 1):
            share = step / steps
            trend = start_log + share * (end_log - start_log)
            log_prices[start + step] = trend + walk[step] - share * walk[-1]

    return {
        day: round(math.exp(log_price), 2)
        for day, log_price in zip(days, log_prices, strict=True)
    }


def main() -> None:
    days = weekdays_between(FIRST_DAY, LAST_DAY)
    anchors: dict[str, dict[date, float]] = {}
    for _, trade in read_transactions(DATA_DIR / "transactions.csv"):
        anchors.setdefault(trade.ticker, {})[trade.trade_date] = trade.price

    rng = random.Random(SEED)
    with (DATA_DIR / "prices.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["ticker", "price_date", "close"])
        for ticker in sorted(anchors):
            ticker_anchors = anchors[ticker]
            first_trade_price = ticker_anchors[min(ticker_anchors)]
            ticker_anchors.setdefault(FIRST_DAY, first_trade_price)
            ticker_anchors[LAST_DAY] = LAST_CLOSES[ticker]
            volatility = DAILY_VOLATILITY.get(ticker, DEFAULT_DAILY_VOLATILITY)
            closes = simulate_closes(days, ticker_anchors, volatility, rng)
            for day, close in closes.items():
                writer.writerow([ticker, day.isoformat(), f"{close:.2f}"])
    print(f"Wrote {len(anchors)} tickers x {len(days)} days to data/prices.csv")


if __name__ == "__main__":
    main()
