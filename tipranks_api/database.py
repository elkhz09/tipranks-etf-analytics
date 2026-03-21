import sqlite3


ETF_INFO_COLUMNS = [
    "etf_ticker",
    "etf_name",
    "etf_index",
    "segment",
    "asset_class",
    "geo_exposure",
    "niche",
    "focus",
    "holdings",
    "price",
    "expense_ratio",
    "dividend_yield",
    "one_year_return",
    "beta",
    "smart_score",
    "top_analyst_rating",
    "top_analyst_rating_signal",
    "top_analyst_price_target",
    "top_analyst_price_target_upside",
    "hedge_fund_signal",
    "hedge_fund_score",
    "insider_signal",
    "insider_score",
    "news_sentiment_signal",
    "news_sentiment_score",
    "top_investor_signal",
    "top_investor_score",
    "blogger_signal",
]

ETF_HOLDING_COLUMNS = [
    "etf_ticker",
    "holding_ticker",
    "stock_name",
    "weight",
    "price",
    "holding_smart_score",
    "top_analyst_rating",
    "top_analyst_rating_id",
    "top_analyst_price_target",
    "top_analyst_price_target_upside",
    "hedge_fund_rating",
    "hedge_fund_rating_id",
    "hedge_fund_score",
    "insider_rating",
    "insider_rating_id",
    "insider_score",
    "blogger_rating",
    "blogger_rating_id",
    "news_sentiment_score",
]

UNIQUE_HOLDING_COLUMNS = [
    "stock_ticker",
    "stock_name",
    "price",
    "holding_smart_score",
    "top_analyst_rating",
    "top_analyst_rating_id",
    "top_analyst_price_target",
    "top_analyst_price_target_upside",
    "hedge_fund_rating",
    "hedge_fund_rating_id",
    "hedge_fund_score",
    "insider_rating",
    "insider_rating_id",
    "insider_score",
    "blogger_rating",
    "blogger_rating_id",
    "news_sentiment_score",
    "ETFs",
]


class TipRanksDB:
    """
    SQLite-backed storage for ETF metadata, ETF holdings, and derived tables.
    """

    def __init__(self, db_path="etf_database.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, uri=db_path.startswith("file:"))
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.conn.close()

    def _create_tables(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS etf_info (
                etf_ticker TEXT PRIMARY KEY,
                etf_name TEXT,
                etf_index TEXT,
                segment TEXT,
                asset_class TEXT,
                geo_exposure TEXT,
                niche TEXT,
                focus TEXT,
                holdings INTEGER,
                price REAL,
                expense_ratio REAL,
                dividend_yield REAL,
                one_year_return REAL,
                beta REAL,
                smart_score INTEGER,
                top_analyst_rating TEXT,
                top_analyst_rating_signal INTEGER,
                top_analyst_price_target REAL,
                top_analyst_price_target_upside REAL,
                hedge_fund_signal TEXT,
                hedge_fund_score REAL,
                insider_signal TEXT,
                insider_score REAL,
                news_sentiment_signal TEXT,
                news_sentiment_score REAL,
                top_investor_signal TEXT,
                top_investor_score REAL,
                blogger_signal TEXT
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS etf_holdings (
                etf_ticker TEXT,
                holding_ticker TEXT,
                stock_name TEXT,
                weight REAL,
                price REAL,
                holding_smart_score INTEGER,
                top_analyst_rating TEXT,
                top_analyst_rating_id INTEGER,
                top_analyst_price_target REAL,
                top_analyst_price_target_upside REAL,
                hedge_fund_rating TEXT,
                hedge_fund_rating_id INTEGER,
                hedge_fund_score REAL,
                insider_rating TEXT,
                insider_rating_id INTEGER,
                insider_score REAL,
                blogger_rating TEXT,
                blogger_rating_id INTEGER,
                news_sentiment_score REAL,
                PRIMARY KEY (etf_ticker, holding_ticker),
                FOREIGN KEY (etf_ticker) REFERENCES etf_info (etf_ticker)
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS unique_holdings (
                stock_ticker TEXT PRIMARY KEY,
                stock_name TEXT,
                price REAL,
                holding_smart_score INTEGER,
                top_analyst_rating TEXT,
                top_analyst_rating_id INTEGER,
                top_analyst_price_target REAL,
                top_analyst_price_target_upside REAL,
                hedge_fund_rating TEXT,
                hedge_fund_rating_id INTEGER,
                hedge_fund_score REAL,
                insider_rating TEXT,
                insider_rating_id INTEGER,
                insider_score REAL,
                blogger_rating TEXT,
                blogger_rating_id INTEGER,
                news_sentiment_score REAL,
                ETFs TEXT
            )
            """
        )
        self.conn.commit()

    def _rows_from_records(self, records, columns):
        return [tuple(record.get(column) for column in columns) for record in records]

    def store_etf_data(self, etf_data):
        """
        Insert or update ETF metadata rows.
        """
        if not etf_data:
            return

        placeholders = ",".join(["?"] * len(ETF_INFO_COLUMNS))
        self.cursor.executemany(
            f"INSERT OR REPLACE INTO etf_info ({','.join(ETF_INFO_COLUMNS)}) VALUES ({placeholders})",
            self._rows_from_records(etf_data, ETF_INFO_COLUMNS),
        )
        self.conn.commit()

    def store_etf_holdings(self, holdings):
        """
        Insert or update ETF holding rows.
        """
        if not holdings:
            return

        placeholders = ",".join(["?"] * len(ETF_HOLDING_COLUMNS))
        self.cursor.executemany(
            f"INSERT OR REPLACE INTO etf_holdings ({','.join(ETF_HOLDING_COLUMNS)}) VALUES ({placeholders})",
            self._rows_from_records(holdings, ETF_HOLDING_COLUMNS),
        )
        self.conn.commit()

    def get_all_etf_tickers(self):
        """
        Return all ETF tickers currently stored in the database.
        """
        self.cursor.execute("SELECT etf_ticker FROM etf_info ORDER BY etf_ticker")
        return [row[0] for row in self.cursor.fetchall()]

    def extract_unique_holdings(self):
        """
        Collapse ETF holdings down to one row per stock ticker.
        """
        self.cursor.execute(
            """
            SELECT
                holding_ticker AS stock_ticker,
                MIN(stock_name) AS stock_name,
                MAX(price) AS price,
                MAX(holding_smart_score) AS holding_smart_score,
                MAX(top_analyst_rating) AS top_analyst_rating,
                MAX(top_analyst_rating_id) AS top_analyst_rating_id,
                MAX(top_analyst_price_target) AS top_analyst_price_target,
                MAX(top_analyst_price_target_upside) AS top_analyst_price_target_upside,
                MAX(hedge_fund_rating) AS hedge_fund_rating,
                MAX(hedge_fund_rating_id) AS hedge_fund_rating_id,
                MAX(hedge_fund_score) AS hedge_fund_score,
                MAX(insider_rating) AS insider_rating,
                MAX(insider_rating_id) AS insider_rating_id,
                MAX(insider_score) AS insider_score,
                MAX(blogger_rating) AS blogger_rating,
                MAX(blogger_rating_id) AS blogger_rating_id,
                MAX(news_sentiment_score) AS news_sentiment_score,
                GROUP_CONCAT(DISTINCT etf_ticker) AS ETFs
            FROM etf_holdings
            GROUP BY holding_ticker
            """
        )
        unique_holdings = self.cursor.fetchall()
        if not unique_holdings:
            return 0

        placeholders = ",".join(["?"] * len(UNIQUE_HOLDING_COLUMNS))
        self.cursor.executemany(
            f"INSERT OR REPLACE INTO unique_holdings ({','.join(UNIQUE_HOLDING_COLUMNS)}) VALUES ({placeholders})",
            unique_holdings,
        )
        self.conn.commit()
        return len(unique_holdings)

    def replace_table_from_dataframe(self, dataframe, table_name):
        """
        Replace a derived table such as `portfolio` from a pandas DataFrame.
        """
        dataframe.to_sql(table_name, self.conn, if_exists="replace", index=False)
        self.conn.commit()

    def update_etf_data(self, tipranks_api):
        """
        Refresh all stored ETFs and their holdings through the API client.
        """
        etf_tickers = self.get_all_etf_tickers()
        if not etf_tickers:
            return []

        updated_etf_data = tipranks_api.fetch_etf_data(etf_tickers)
        self.store_etf_data(updated_etf_data)

        for etf in updated_etf_data:
            etf_ticker = etf["etf_ticker"]
            total_holdings = etf.get("holdings") or 0
            if not total_holdings:
                continue

            updated_holdings = tipranks_api.fetch_etf_holdings(etf_ticker, total_holdings)
            self.store_etf_holdings(updated_holdings)

        self.extract_unique_holdings()
        return updated_etf_data
