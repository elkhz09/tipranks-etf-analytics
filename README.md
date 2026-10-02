# ETF Look-Through

This answers one question about a portfolio of ETFs: which companies do I
actually own, and how much of my exposure is the same company bought three times?
It fetches each fund's holdings from TipRanks' undocumented mobile API, stores
them in SQLite, then multiplies ETF weights through to estimated stock-level
weights so a nine-fund allocation can be read as a ranked list of companies.

I wrote it because I held funds across China, India, Singapore, semiconductors,
robotics and US beta, and could not answer how much of that was one position
wearing six names. The look-through is the part worth reading. The API client is
request plumbing against an endpoint that can change without notice.

Python, pandas, SQLite, `requests`. No scraping stack and no browser.

---

## What it does

```bash
# which ETFs are already stored
python scripts/portfolio_cli.py coverage ASHR FXI MCHI EWS ARTY BOTZ SOXX INDA SPY

# top-holding overlap across a thematic set
python scripts/portfolio_cli.py top-holdings SOXX BOTZ ARTY --limit 15

# stock-level exposure from a multi-ETF allocation
python scripts/portfolio_cli.py portfolio-weight SPY=20 SOXX=15 BOTZ=10 ARTY=10 --top 25
```

- **Look-through.** Allocations are normalised, each fund's holding weights are
  scaled by its share of the portfolio, and the results are summed per company.
  Allocations can be given as fractions or as percentages; either is normalised.
- **Overlap.** Top holdings across a set of funds, with a count of how many of
  them hold each company. Thematic funds reuse the same large caps, and the
  overlap is consistently larger than the fund names suggest.
- **Ingestion.** Fund metadata and holdings into a local database, with a derived
  one-row-per-company table.
- **Coverage.** Which requested tickers are in the database and which are not, so
  an analysis runs on a known subset instead of silently dropping funds.

## What was hard

**The API is undocumented and paged ten rows at a time.** Nothing describes the
response shape, so the field mapping was read off live responses. A 500-holding
fund is 50 sequential requests, rate-limited by a half-second sleep, and the
client sends the iPhone app's own headers to get a response at all.

**Price is not returned, so it is derived.** The holdings endpoint gives an
analyst price target and a percentage upside but no spot price. The client
recovers one by dividing the target by `1 + upside/100`. That is arithmetic on two
third-party estimates and should be treated as such.

**One company, several funds, several views of it.** The same stock arrives once
per fund, each copy carrying its own snapshot of score, rating and price. The
derived table has to pick. It takes the maximum of each column independently,
which is simple, stable, and wrong in a way described below.

---

## Starting from an empty database

`data/` is not in the repository, so a fresh clone has no database and every CLI
example above will fail until one is built. Populating it needs a TipRanks
account. The client takes the credentials as constructor arguments:

```python
api = TipRanksAPI(email=..., password=...)       # posts to /api/iOS/login2
db = TipRanksDB("data/etf_database.db")
db.update_etf_data(api)
```

Nothing in the code reads them from the environment. The notebook suggests
`TIPRANKS_EMAIL` and `TIPRANKS_PASSWORD` in a commented-out cell and that is the
whole of it, so wire them up yourself and keep them out of the repository.

The client talks to `mobile.tipranks.com` and sends the iPhone app's user agent to
get a response. It is not a public data product and has no published terms for
this use. Check your own account terms before pointing it anywhere, and keep the
volume low. The last two cells of `notebooks/portfolio_exploration.ipynb` show the
fetch-and-store path.

## Tests

```bash
pip install -r requirements.txt
python -m unittest discover -s tests
```

Five tests, all passing. They build a temporary database and cover storage, the
derived table, the three analytics queries and the snapshot join, so they run on a
fresh clone with no credentials.

They do not cover the API client. All 324 lines of it, including the retry path
and every field mapping, are exercised only by running it against the live
service. The tests substitute a `FakeAPI` instead. That is the largest untested
surface here and the one most likely to break, because it depends on a response
shape nobody published.

---

## What it does not do

No prices, no returns, no risk model, no optimiser. Weights in, estimated
exposures out. Holdings are a snapshot from whenever they were fetched, and
nothing tracks drift or rebalancing.

## Where it is wrong, specifically

**The derived company table can mix sources.** `extract_unique_holdings` groups by
ticker and takes `MAX()` of each column separately. If two funds report the same
company with different smart scores and different prices, the row gets the highest
of each, which may be a score from one fund's snapshot beside a price from
another's. No single row is guaranteed to come from one source. Grouping on the
most recent fetch per company would be the fix.

**Look-through assumes the stored holdings are complete.** Weights are scaled and
summed with no check that each fund's holdings sum to roughly 100%. Passing the
`--limit` option, or a fetch that stopped early, silently understates every
exposure rather than failing or renormalising.

**One analytics method writes to the database.** `build_portfolio_snapshot`
replaces a `portfolio` table as a side effect of being called. A read method that
mutates storage is a trap for anyone who assumes the rest of the class is
read-only.

**Scores carried into the output are TipRanks'.** Smart score, analyst consensus,
hedge fund and insider ratings pass through unchanged. They are a vendor's
opinion, presented in these tables beside weights that are arithmetic.

**`querydb.py` and `TipRanksQueryDB` are legacy.** A one-line re-export and an
alias kept so older notebooks still import. New code should use
`PortfolioAnalytics`.

---

## Layout

```
tipranks_api/
  api.py          client: fund metadata, holdings, stock technicals
  database.py     SQLite storage and the derived company table
  analytics.py    overlap, look-through, coverage
  querydb.py      legacy re-export shim
scripts/
  portfolio_cli.py            the three queries above
notebooks/
  portfolio_exploration.ipynb the same workflow with commentary
tests/
  test_database_and_queries.py storage and analytics, temp database
```

The portfolio in the notebook is an illustrative allocation, not a real one.

MIT licensed.
