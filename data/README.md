# Sample data (illustrative only)

All clients are fictional and every price is made up. The tickers are real
Canadian listings, used only so the example looks familiar. Nothing here is real
market data, real client information or a recommendation.

| File | One row per | Columns |
|---|---|---|
| `clients.csv` | client | name, risk (`Conservative`, `Balanced` or `Growth`) |
| `transactions.csv` | trade | client, trade_date (YYYY-MM-DD), ticker, side (`Buy` or `Sell`), quantity, price |

Every client in `transactions.csv` must appear in `clients.csv`, and no client
may sell more shares than they hold at the time. All amounts are CAD.

Load into MySQL with `python -m wealth_analytics.sample_data`
(add `--reset` to wipe and reload).
