# ETF Research & Portfolio Analytics

Python tool for ETF holdings research, portfolio look-through analysis, and stock-level exposure decomposition.

---

## What This Project Demonstrates

Relevant to asset management, quant research, and portfolio analytics roles:

- **Portfolio look-through** — converts ETF weights into estimated stock-level exposures across a multi-ETF portfolio
- **Holdings overlap analysis** — identifies repeated stock exposures across thematic and regional ETFs
- **Data engineering** — API integration, SQLite schema design, ETL-style ingestion pipeline
- **Research workflow** — reproducible notebook exploration with CLI tooling for quick queries
- **Python packaging** — structured as an installable package with tests

---

## Core Use Cases

**ETF overlap analysis**
Compare top holdings across ETFs (e.g. `SOXX`, `BOTZ`, `ARTY`) to identify concentration risk from repeated exposures.

**Portfolio look-through**
Convert a multi-ETF allocation like `SPY=20 SOXX=15 BOTZ=10 ARTY=10` into estimated stock-level weights.

**Thematic sleeve research**
Explore a mixed portfolio spanning China, India, Singapore, semiconductors, robotics, AI, and US beta through ETFs including `ASHR`, `FXI`, `MCHI`, `EWS`, `ARTY`, `BOTZ`, `SOXX`, `INDA`, `SPY`.

---

## Repository Structure

```
tipranks_api/
  api.py          TipRanks API client (ETF metadata, holdings, technicals)
  database.py     SQLite storage layer (ETF metadata, holdings, derived tables)
  analytics.py    Overlap analysis, portfolio look-through, coverage helpers
  querydb.py      Query helpers
scripts/
  portfolio_cli.py   CLI entry point for quick research tasks
notebooks/
  portfolio_exploration.ipynb   Notebook-driven research workflow
tests/
  test_database_and_queries.py
data/
  etf_database.db
```

**Stack:** Python · pandas · SQLite · Jupyter · Playwright

---

## CLI Examples

```bash
# Check which ETFs are already in the local database
python scripts/portfolio_cli.py coverage ASHR FXI MCHI EWS ARTY BOTZ SOXX INDA SPY

# Compare top holdings across ETFs
python scripts/portfolio_cli.py top-holdings SOXX BOTZ ARTY --limit 15

# Estimate stock-level exposure from a multi-ETF portfolio
python scripts/portfolio_cli.py portfolio-weight SPY=20 SOXX=15 BOTZ=10 ARTY=10 --top 25
```

---

## Notebook Workflow

The notebook in `notebooks/portfolio_exploration.ipynb` demonstrates a realistic research workflow:

1. Load a multi-region and thematic ETF portfolio
2. Check database coverage for the ETF set
3. Analyse top-holding overlap for available ETFs
4. Estimate stock-level portfolio exposure after combining ETF weights
5. Identify gaps in database coverage for next fetch

---

## Quick Start

```bash
pip install -r requirements.txt
python -m unittest discover -s tests
```
