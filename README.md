# ETF Research & Portfolio Analytics

Pulls ETF holdings from TipRanks, stores them in SQLite, and works out what a
multi-ETF portfolio actually owns at the stock level.

The question it answers: if I hold nine ETFs across China, India, Singapore,
semiconductors, robotics and US beta, which underlying names am I really exposed
to, and how much of that exposure is the same company bought three times?

---

## What it does

- **Look-through.** Converts ETF weights into estimated stock-level weights, so
  `SPY=20 SOXX=15 BOTZ=10 ARTY=10` becomes a ranked list of underlying holdings.
- **Overlap.** Compares top holdings across a set of ETFs. Thematic funds reuse
  the same large caps, and the overlap is usually larger than it looks from the
  fund names.
- **Ingestion.** Fetches ETF metadata and holdings, then stores them in a local
  SQLite database with derived tables for querying.
- **Coverage check.** Reports which requested tickers are already in the database
  and which still need fetching, so analysis runs on a known subset rather than
  silently dropping tickers.

## What it does not do

No prices, no returns, no risk model, no optimiser. Weights in, estimated
exposures out. Holdings are a snapshot from whenever they were fetched; nothing
tracks drift or rebalances.

---

## Starting from an empty database

`data/` is not in the repository, so a fresh clone has no database and the CLI
examples below will fail until one is built. Populating it needs TipRanks
credentials:

```bash
export TIPRANKS_EMAIL=...
export TIPRANKS_PASSWORD=...
```

The client talks to TipRanks' mobile API, which is undocumented and not a public
data product. Check your account terms before pointing it at anything, and keep
the request volume low. Nothing in this repository will work without an account.

The last two cells of the notebook show the fetch-and-store path. Once the
database exists, the CLI works:

```bash
# which ETFs are already stored
python scripts/portfolio_cli.py coverage ASHR FXI MCHI EWS ARTY BOTZ SOXX INDA SPY

# top-holding overlap across a thematic set
python scripts/portfolio_cli.py top-holdings SOXX BOTZ ARTY --limit 15

# stock-level exposure from a multi-ETF allocation
python scripts/portfolio_cli.py portfolio-weight SPY=20 SOXX=15 BOTZ=10 ARTY=10 --top 25
```

The example portfolio used in the notebook is an illustrative allocation, not a
real one.

---

## Layout

```
tipranks_api/
  api.py          TipRanks client — ETF metadata, holdings, stock technicals
  database.py     SQLite storage and derived tables
  analytics.py    overlap, look-through, coverage
  querydb.py      re-export shim for analytics
scripts/
  portfolio_cli.py   CLI for the three queries above
notebooks/
  portfolio_exploration.ipynb   the same workflow, with commentary
tests/
  test_database_and_queries.py  storage and analytics, against a temp database
```

Python, pandas, SQLite, Jupyter. No scraping stack — the client is plain
`requests` against a JSON API.

---

## Tests

```bash
pip install -r requirements.txt
python -m unittest discover -s tests
```

Five tests covering storage and the analytics queries. They build their own
temporary database, so they run on a fresh clone with no credentials.

---

## Notes

Written to get a concrete answer about my own ETF overlap, then tidied into a
package. The analytics layer is the part worth reading; the API client is
ordinary request plumbing against an endpoint that may change without notice.

MIT licensed.
