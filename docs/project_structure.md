# Project Structure

This repository is organized as a compact research project rather than a loose collection of scripts.

## Main folders

- `tipranks_api/`: reusable Python package for API access, storage, and analytics
- `data/`: local working database used by the CLI and notebook
- `scripts/`: lightweight command-line entry points
- `notebooks/`: exploratory analysis and portfolio research notebooks
- `tests/`: unit tests for storage and analytics workflows
- `docs/`: supporting documentation for structure and usage

## Design intent

The code is split into layers:

1. Ingestion layer: authenticate and pull ETF or stock data from TipRanks.
2. Storage layer: save ETF metadata and holdings into SQLite.
3. Analytics layer: compare ETFs, aggregate exposures, and build portfolio views.
4. Exploration layer: notebooks and CLI tools for research workflows.
