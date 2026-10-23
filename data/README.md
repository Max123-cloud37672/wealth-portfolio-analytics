# Sample data (illustrative only)

All clients are fictional and every price is made up. The tickers are real
Canadian listings, used only so the example looks familiar. Nothing here is real
market data, real client information or a recommendation.

| File | One row per | Columns |
|---|---|---|
| `clients.csv` | client | name, risk (`Conservative`, `Balanced` or `Growth`) |
| `transactions.csv` | trade | client, trade_date (YYYY-MM-DD), ticker, side (`Buy` or `Sell`), quantity, price |
| `securities.csv` | security | ticker, name, asset_type (`Stock` or `ETF`), sector |
| `prices.csv` | ticker per weekday | ticker, price_date (YYYY-MM-DD), close |

Every client in `transactions.csv` must appear in `clients.csv`, every ticker in
`securities.csv`, and no client may sell more shares than they hold at the time.
All amounts are CAD.

`prices.csv` is simulated, not downloaded: each price series passes exactly
through the sample trade prices, with random daily moves in between (see
`src/wealth_analytics/price_simulation.py`). Regenerate it with
`python -m wealth_analytics.price_simulation`.

Load into MySQL with `python -m wealth_analytics.sample_data`
(add `--reset` to wipe and reload).
