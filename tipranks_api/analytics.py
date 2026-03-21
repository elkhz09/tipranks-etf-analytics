import sqlite3

import pandas as pd


TOP_HOLDINGS_COLUMNS = [
    "ticker",
    "stock_name",
    "smart_score",
    "analyst_rating",
    "ETF Count",
]

PORTFOLIO_WEIGHT_COLUMNS = [
    "ticker",
    "stock_name",
    "smart_score",
    "analyst_rating",
    "Total Portfolio Weight",
]


class PortfolioAnalytics:
    """
    Query helpers built on top of the local ETF SQLite database.
    """

    def __init__(self, db_path="etf_database.db"):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path, uri=self.db_path.startswith("file:"))

    def get_etf_universe(self):
        """
        Return the ETFs currently stored in the local database.
        """
        with self._connect() as conn:
            try:
                return pd.read_sql_query(
                    """
                    SELECT
                        etf_ticker,
                        etf_name,
                        holdings,
                        expense_ratio,
                        smart_score,
                        one_year_return
                    FROM etf_info
                    ORDER BY etf_ticker
                    """,
                    conn,
                )
            except Exception:
                return pd.DataFrame(
                    columns=[
                        "etf_ticker",
                        "etf_name",
                        "holdings",
                        "expense_ratio",
                        "smart_score",
                        "one_year_return",
                    ]
                )

    def summarize_requested_etfs(self, tickers):
        """
        Show which requested ETFs are already available in the local database.
        """
        if isinstance(tickers, str):
            tickers = [tickers]

        requested = [ticker.upper() for ticker in tickers if ticker]
        if not requested:
            return pd.DataFrame(columns=["requested_ticker", "available", "etf_name", "holdings"])

        universe = self.get_etf_universe()
        if universe.empty:
            return pd.DataFrame(
                {
                    "requested_ticker": requested,
                    "available": [False] * len(requested),
                    "etf_name": [None] * len(requested),
                    "holdings": [None] * len(requested),
                }
            )

        indexed_universe = universe.set_index("etf_ticker")
        rows = []
        for ticker in requested:
            if ticker in indexed_universe.index:
                row = indexed_universe.loc[ticker]
                rows.append(
                    {
                        "requested_ticker": ticker,
                        "available": True,
                        "etf_name": row["etf_name"],
                        "holdings": row["holdings"],
                    }
                )
            else:
                rows.append(
                    {
                        "requested_ticker": ticker,
                        "available": False,
                        "etf_name": None,
                        "holdings": None,
                    }
                )

        return pd.DataFrame(rows)

    def get_top_holdings(self, etfs, n=15):
        """
        Return the top holdings for each ETF and highlight overlap across them.
        """
        if isinstance(etfs, str):
            etfs = [etfs]
        etfs = [etf.upper() for etf in etfs if etf]
        if not etfs:
            return pd.DataFrame(columns=TOP_HOLDINGS_COLUMNS)

        etf_frames = {}
        with self._connect() as conn:
            for etf in etfs:
                df = pd.read_sql_query(
                    """
                    SELECT
                        holding_ticker AS ticker,
                        stock_name AS stock_name,
                        holding_smart_score AS smart_score,
                        top_analyst_rating AS analyst_rating,
                        weight
                    FROM etf_holdings
                    WHERE etf_ticker = ?
                    ORDER BY weight DESC, holding_ticker ASC
                    LIMIT ?
                    """,
                    conn,
                    params=(etf, n),
                )
                if df.empty:
                    continue

                df[f"{etf} Weight"] = df["weight"] * 100
                etf_frames[etf] = df.drop(columns=["weight"]).set_index(
                    ["ticker", "stock_name", "smart_score", "analyst_rating"]
                )

        if not etf_frames:
            return pd.DataFrame(columns=TOP_HOLDINGS_COLUMNS + [f"{etf} Weight" for etf in etfs])

        final_df = None
        for df in etf_frames.values():
            final_df = df if final_df is None else final_df.join(df, how="outer")

        final_df = final_df.fillna("NA")
        weight_cols = [col for col in final_df.columns if col.endswith("Weight")]
        for col in weight_cols:
            final_df[col] = final_df[col].apply(lambda value: 0.0 if value == "NA" else float(value))

        final_df["ETF Count"] = final_df[weight_cols].gt(0).sum(axis=1)
        final_df["Max Weight"] = final_df[weight_cols].max(axis=1)
        final_df = final_df.sort_values(by=["ETF Count", "Max Weight"], ascending=[False, False])

        for col in weight_cols:
            final_df[col] = final_df[col].apply(lambda value: f"{value:.2f}%" if value > 0 else "NA")

        final_df = final_df.drop(columns=["Max Weight"]).reset_index()
        return final_df

    def get_portfolio_weight(self, etf_allocations, n=None, top=20):
        """
        Estimate stock-level portfolio weights from ETF allocations.

        Allocations can be passed either as fractions (0.6, 0.4) or whole
        percentages (60, 40). The method normalizes them either way.
        """
        if not etf_allocations:
            return pd.DataFrame(columns=PORTFOLIO_WEIGHT_COLUMNS)

        normalized_allocations = {
            etf.upper(): float(allocation)
            for etf, allocation in etf_allocations.items()
            if etf and allocation is not None
        }
        allocation_total = sum(normalized_allocations.values())
        if allocation_total <= 0:
            return pd.DataFrame(columns=PORTFOLIO_WEIGHT_COLUMNS)

        all_etf_frames = []
        with self._connect() as conn:
            for etf, allocation in normalized_allocations.items():
                query = """
                    SELECT
                        holding_ticker AS ticker,
                        stock_name AS stock_name,
                        weight,
                        top_analyst_rating AS analyst_rating,
                        holding_smart_score AS smart_score
                    FROM etf_holdings
                    WHERE etf_ticker = ?
                    ORDER BY weight DESC, holding_ticker ASC
                """
                params = [etf]
                if n:
                    query += " LIMIT ?"
                    params.append(n)

                df = pd.read_sql_query(query, conn, params=params)
                if df.empty:
                    continue

                normalized_allocation = allocation / allocation_total
                df["Adjusted Weight"] = df["weight"] * normalized_allocation
                all_etf_frames.append(df.drop(columns=["weight"]))

        if not all_etf_frames:
            return pd.DataFrame(columns=PORTFOLIO_WEIGHT_COLUMNS)

        portfolio_df = (
            pd.concat(all_etf_frames, ignore_index=True)
            .groupby(["ticker", "stock_name", "smart_score", "analyst_rating"], as_index=False)["Adjusted Weight"]
            .sum()
            .sort_values(by="Adjusted Weight", ascending=False)
        )

        if top is not None:
            portfolio_df = portfolio_df.head(top).copy()

        portfolio_df["Total Portfolio Weight"] = (portfolio_df["Adjusted Weight"] * 100).map(lambda value: f"{value:.2f}%")
        return portfolio_df.drop(columns=["Adjusted Weight"]).reset_index(drop=True)

    def build_portfolio_snapshot(self, api, table_name="portfolio", tickers=None):
        """
        Join `unique_holdings` with stock technical indicators and persist the
        result back into the same SQLite database.
        """
        with self._connect() as conn:
            unique_holdings = pd.read_sql_query(
                """
                SELECT
                    stock_ticker AS ticker,
                    stock_name AS name,
                    price,
                    holding_smart_score,
                    top_analyst_rating,
                    top_analyst_rating_id,
                    top_analyst_price_target,
                    top_analyst_price_target_upside,
                    hedge_fund_rating,
                    hedge_fund_rating_id,
                    hedge_fund_score,
                    insider_rating,
                    insider_rating_id,
                    insider_score,
                    blogger_rating,
                    blogger_rating_id,
                    news_sentiment_score,
                    ETFs
                FROM unique_holdings
                ORDER BY stock_ticker
                """,
                conn,
            )

        if unique_holdings.empty:
            return unique_holdings

        if tickers is not None:
            requested = {ticker.upper() for ticker in tickers}
            unique_holdings = unique_holdings[unique_holdings["ticker"].isin(requested)].copy()

        if unique_holdings.empty:
            return unique_holdings

        technicals = api.fetch_stock_technicals(unique_holdings["ticker"].tolist())
        portfolio_df = unique_holdings.merge(technicals, on="ticker", how="left")

        with self._connect() as conn:
            portfolio_df.to_sql(table_name, conn, if_exists="replace", index=False)

        return portfolio_df


class TipRanksQueryDB(PortfolioAnalytics):
    """
    Backward-compatible class name kept for older notebooks and scripts.
    """
