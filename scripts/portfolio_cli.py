import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tipranks_api import TipRanksQueryDB


DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "etf_database.db"


def parse_allocations(values):
    allocations = {}
    for value in values:
        ticker, raw_allocation = value.split("=", maxsplit=1)
        allocations[ticker.strip().upper()] = float(raw_allocation.strip())
    return allocations


def main():
    parser = argparse.ArgumentParser(
        description="Analyze ETF overlap and portfolio exposure using the local TipRanks SQLite database."
    )
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help="Path to the ETF database. Defaults to data/etf_database.db.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    top_parser = subparsers.add_parser("top-holdings", help="Compare top holdings across ETFs.")
    top_parser.add_argument("etfs", nargs="+", help="ETF tickers to compare.")
    top_parser.add_argument("--limit", type=int, default=15, help="Top holdings to pull per ETF.")

    weight_parser = subparsers.add_parser("portfolio-weight", help="Estimate stock-level portfolio exposure.")
    weight_parser.add_argument(
        "allocations",
        nargs="+",
        help="ETF allocations in TICKER=VALUE format, for example SPY=40 SOXX=20 BOTZ=10.",
    )
    weight_parser.add_argument("--limit", type=int, default=None, help="Optional top holdings limit per ETF.")
    weight_parser.add_argument("--top", type=int, default=20, help="Number of stock rows to return.")

    coverage_parser = subparsers.add_parser("coverage", help="Show which requested ETFs are available in the DB.")
    coverage_parser.add_argument("etfs", nargs="+", help="ETF tickers to check.")

    args = parser.parse_args()
    query = TipRanksQueryDB(args.db)

    if args.command == "top-holdings":
        result = query.get_top_holdings(args.etfs, n=args.limit)
    elif args.command == "portfolio-weight":
        result = query.get_portfolio_weight(
            parse_allocations(args.allocations),
            n=args.limit,
            top=args.top,
        )
    else:
        result = query.summarize_requested_etfs(args.etfs)

    if result.empty:
        print("No rows returned. Check the database path and ETF tickers.")
        return

    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
