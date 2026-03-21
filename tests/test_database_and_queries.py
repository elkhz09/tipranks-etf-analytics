import unittest
import uuid

import pandas as pd

from tipranks_api import TipRanksDB, TipRanksQueryDB


ETF_DATA = [
    {
        "etf_ticker": "VOO",
        "etf_name": "Vanguard S&P 500 ETF",
        "etf_index": "S&P 500",
        "segment": "Large Cap",
        "asset_class": "Equity",
        "geo_exposure": "US",
        "niche": None,
        "focus": None,
        "holdings": 3,
        "price": 500.0,
        "expense_ratio": 0.03,
        "dividend_yield": 1.2,
        "one_year_return": 10.0,
        "beta": 1.0,
        "smart_score": 8,
        "top_analyst_rating": "Buy",
        "top_analyst_rating_signal": 2,
        "top_analyst_price_target": 520.0,
        "top_analyst_price_target_upside": 4.0,
        "hedge_fund_signal": "Positive",
        "hedge_fund_score": 8.1,
        "insider_signal": "Neutral",
        "insider_score": 5.0,
        "news_sentiment_signal": "Positive",
        "news_sentiment_score": 7.0,
        "top_investor_signal": "Positive",
        "top_investor_score": 8.0,
        "blogger_signal": "Bullish",
    },
    {
        "etf_ticker": "QQQ",
        "etf_name": "Invesco QQQ",
        "etf_index": "Nasdaq 100",
        "segment": "Growth",
        "asset_class": "Equity",
        "geo_exposure": "US",
        "niche": None,
        "focus": None,
        "holdings": 3,
        "price": 450.0,
        "expense_ratio": 0.20,
        "dividend_yield": 0.8,
        "one_year_return": 12.0,
        "beta": 1.1,
        "smart_score": 9,
        "top_analyst_rating": "Buy",
        "top_analyst_rating_signal": 2,
        "top_analyst_price_target": 470.0,
        "top_analyst_price_target_upside": 4.4,
        "hedge_fund_signal": "Positive",
        "hedge_fund_score": 8.8,
        "insider_signal": "Positive",
        "insider_score": 6.0,
        "news_sentiment_signal": "Positive",
        "news_sentiment_score": 7.5,
        "top_investor_signal": "Positive",
        "top_investor_score": 8.5,
        "blogger_signal": "Bullish",
    },
]

ETF_HOLDINGS = [
    {
        "etf_ticker": "VOO",
        "holding_ticker": "AAPL",
        "stock_name": "Apple Inc.",
        "weight": 0.07,
        "price": 180.0,
        "holding_smart_score": 9,
        "top_analyst_rating": "Buy",
        "top_analyst_rating_id": 2,
        "top_analyst_price_target": 200.0,
        "top_analyst_price_target_upside": 11.0,
        "hedge_fund_rating": "Positive",
        "hedge_fund_rating_id": 2,
        "hedge_fund_score": 8.0,
        "insider_rating": "Neutral",
        "insider_rating_id": 1,
        "insider_score": 5.0,
        "blogger_rating": "Bullish",
        "blogger_rating_id": 2,
        "news_sentiment_score": 7.0,
    },
    {
        "etf_ticker": "VOO",
        "holding_ticker": "MSFT",
        "stock_name": "Microsoft Corp.",
        "weight": 0.06,
        "price": 410.0,
        "holding_smart_score": 10,
        "top_analyst_rating": "Buy",
        "top_analyst_rating_id": 2,
        "top_analyst_price_target": 430.0,
        "top_analyst_price_target_upside": 5.0,
        "hedge_fund_rating": "Positive",
        "hedge_fund_rating_id": 2,
        "hedge_fund_score": 9.0,
        "insider_rating": "Neutral",
        "insider_rating_id": 1,
        "insider_score": 5.0,
        "blogger_rating": "Bullish",
        "blogger_rating_id": 2,
        "news_sentiment_score": 8.0,
    },
    {
        "etf_ticker": "QQQ",
        "holding_ticker": "MSFT",
        "stock_name": "Microsoft Corp.",
        "weight": 0.09,
        "price": 410.0,
        "holding_smart_score": 10,
        "top_analyst_rating": "Buy",
        "top_analyst_rating_id": 2,
        "top_analyst_price_target": 430.0,
        "top_analyst_price_target_upside": 5.0,
        "hedge_fund_rating": "Positive",
        "hedge_fund_rating_id": 2,
        "hedge_fund_score": 9.0,
        "insider_rating": "Neutral",
        "insider_rating_id": 1,
        "insider_score": 5.0,
        "blogger_rating": "Bullish",
        "blogger_rating_id": 2,
        "news_sentiment_score": 8.0,
    },
    {
        "etf_ticker": "QQQ",
        "holding_ticker": "NVDA",
        "stock_name": "NVIDIA Corp.",
        "weight": 0.08,
        "price": 900.0,
        "holding_smart_score": 10,
        "top_analyst_rating": "Buy",
        "top_analyst_rating_id": 2,
        "top_analyst_price_target": 950.0,
        "top_analyst_price_target_upside": 5.5,
        "hedge_fund_rating": "Positive",
        "hedge_fund_rating_id": 2,
        "hedge_fund_score": 9.5,
        "insider_rating": "Neutral",
        "insider_rating_id": 1,
        "insider_score": 4.0,
        "blogger_rating": "Bullish",
        "blogger_rating_id": 2,
        "news_sentiment_score": 8.5,
    },
]


class FakeAPI:
    def fetch_stock_technicals(self, tickers):
        return pd.DataFrame(
            [
                {
                    "ticker": ticker,
                    "one_month_gain": 0.1,
                    "three_months_gain": 0.2,
                    "six_months_gain": 0.3,
                    "ytd_gain": 0.4,
                    "volumeAvg10d": 100,
                    "volumeAvg30d": 110,
                    "volumeAvg90d": 120,
                    "emA21d": 10,
                    "emA50d": 11,
                    "movingAvg21d": 12,
                    "movingAvg50d": 13,
                    "movingAvg200d": 14,
                }
                for ticker in tickers
            ]
        )


class DatabaseAndQueryTests(unittest.TestCase):
    def setUp(self):
        self.db_path = f"file:test_db_{uuid.uuid4().hex}?mode=memory&cache=shared"
        self.db = TipRanksDB(self.db_path)
        self.db.store_etf_data(ETF_DATA)
        self.db.store_etf_holdings(ETF_HOLDINGS)

    def tearDown(self):
        self.db.close()

    def test_extract_unique_holdings(self):
        inserted = self.db.extract_unique_holdings()
        self.assertEqual(inserted, 3)

    def test_get_top_holdings(self):
        query = TipRanksQueryDB(self.db_path)
        top_holdings = query.get_top_holdings(["VOO", "QQQ"], n=2)

        self.assertFalse(top_holdings.empty)
        self.assertIn("VOO Weight", top_holdings.columns)
        self.assertIn("QQQ Weight", top_holdings.columns)
        self.assertEqual(top_holdings.iloc[0]["ticker"], "MSFT")
        self.assertEqual(top_holdings.iloc[0]["ETF Count"], 2)

    def test_requested_etf_summary(self):
        query = TipRanksQueryDB(self.db_path)
        summary = query.summarize_requested_etfs(["VOO", "ASHR"])

        self.assertEqual(summary.loc[0, "available"], True)
        self.assertEqual(summary.loc[1, "available"], False)

    def test_get_portfolio_weight(self):
        query = TipRanksQueryDB(self.db_path)
        weights = query.get_portfolio_weight({"VOO": 60, "QQQ": 40}, n=2, top=3)

        self.assertFalse(weights.empty)
        self.assertEqual(weights.iloc[0]["ticker"], "MSFT")
        self.assertTrue(weights.iloc[0]["Total Portfolio Weight"].endswith("%"))

    def test_build_portfolio_snapshot(self):
        self.db.extract_unique_holdings()
        query = TipRanksQueryDB(self.db_path)
        snapshot = query.build_portfolio_snapshot(FakeAPI())

        self.assertFalse(snapshot.empty)
        self.assertIn("movingAvg200d", snapshot.columns)
        self.assertEqual(set(snapshot["ticker"]), {"AAPL", "MSFT", "NVDA"})


if __name__ == "__main__":
    unittest.main()
