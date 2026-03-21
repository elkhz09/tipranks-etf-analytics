import logging
import math
import time
from typing import Any, Literal, Optional, Union, overload

import pandas as pd
import requests


LOGGER = logging.getLogger(__name__)
JsonDict = dict[str, Any]


class TipRanksAPI:
    """
    Small client for the TipRanks mobile API.

    The class focuses on three workflows used elsewhere in this project:
    ETF metadata, ETF holdings, and stock technical indicators.
    """

    def __init__(
        self,
        email=None,
        password=None,
        *,
        base_url="https://mobile.tipranks.com",
        session=None,
        headers=None,
        timeout=30,
        auto_login=True,
    ):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout
        self.headers = {
            "accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "content-type": "application/json; charset=UTF-8",
            "accept-encoding": "gzip",
            "x-platform": "iphone",
            "user-agent": "TipRanksApp/17 CFNetwork/1390 Darwin/22.0.0",
            "accept-language": "en-US,en;q=0.9",
        }
        if headers:
            self.headers.update(headers)

        if auto_login and email and password:
            self.login(email, password)

    @overload
    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[dict[str, Any]] = ...,
        json: Optional[dict[str, Any]] = ...,
        expect_json: Literal[True] = ...,
        retries: int = ...,
        retry_delay: int = ...,
    ) -> JsonDict: ...

    @overload
    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[dict[str, Any]] = ...,
        json: Optional[dict[str, Any]] = ...,
        expect_json: Literal[False],
        retries: int = ...,
        retry_delay: int = ...,
    ) -> requests.Response: ...

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
        expect_json: bool = True,
        retries: int = 5,
        retry_delay: int = 3,
    ) -> Union[JsonDict, requests.Response]:
        """
        Send a request with light retry handling.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        last_error = None

        for attempt in range(1, retries + 1):
            try:
                response = self.session.request(
                    method,
                    url,
                    headers=self.headers,
                    params=params,
                    json=json,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                if not response.text.strip():
                    raise ValueError(f"Empty response returned from {url}")

                return response.json() if expect_json else response
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                LOGGER.warning(
                    "TipRanks request failed for %s on attempt %s/%s: %s",
                    url,
                    attempt,
                    retries,
                    exc,
                )
                if attempt < retries:
                    time.sleep(retry_delay)

        raise RuntimeError(f"TipRanks request failed after {retries} attempts: {url}") from last_error

    def login(self, email: str, password: str) -> None:
        """
        Authenticate the session.
        """
        response = self._request(
            "POST",
            "/api/iOS/login2",
            json={"email": email, "password": password},
            expect_json=False,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Login failed with status code: {response.status_code}")

        LOGGER.info("TipRanks login successful")

    def fetch_etf_data(self, tickers: Union[str, list[str]]) -> list[JsonDict]:
        """
        Fetch ETF metadata for one or more ETF tickers.
        """
        if isinstance(tickers, str):
            tickers = [tickers]
        if not tickers:
            return []

        response = self._request(
            "GET",
            "/api/compare/stocks/",
            params={"tickers": ",".join(tickers)},
        )
        data_list = response.get("data", [])
        extra_data_list = response.get("extraData", [])

        research_by_ticker = {
            item["ticker"]: item.get("research", {})
            for item in extra_data_list
            if item.get("ticker")
        }
        etf_data_by_ticker = {
            item["ticker"]: item.get("etfData", {})
            for item in extra_data_list
            if item.get("ticker")
        }

        etf_results = []
        for etf in data_list:
            etf_ticker = etf.get("ticker")
            if not etf_ticker:
                continue

            research = research_by_ticker.get(etf_ticker, {})
            etf_data = etf_data_by_ticker.get(etf_ticker, {})
            analyst_consensus = etf.get("bestAnalystConsensus") or {}

            etf_results.append(
                {
                    "etf_ticker": etf_ticker,
                    "etf_name": etf.get("companyName"),
                    "etf_index": etf_data.get("indexName"),
                    "segment": etf_data.get("segmentDescription"),
                    "asset_class": etf_data.get("assetClass"),
                    "geo_exposure": etf_data.get("specificGeographicExposure"),
                    "niche": etf_data.get("etfNiche"),
                    "focus": etf_data.get("etfFocus"),
                    "holdings": etf_data.get("etfHoldingsCount"),
                    "price": research.get("price"),
                    "expense_ratio": etf_data.get("expenseRatio"),
                    "dividend_yield": research.get("rawDividendYield"),
                    "one_year_return": research.get("yearlyGain"),
                    "beta": etf_data.get("beta"),
                    "smart_score": research.get("tipRanksScore"),
                    "top_analyst_rating": analyst_consensus.get("consensus"),
                    "top_analyst_rating_signal": analyst_consensus.get("rawConsensus"),
                    "top_analyst_price_target": research.get("bestPriceTarget"),
                    "top_analyst_price_target_upside": research.get("bestUpside"),
                    "hedge_fund_signal": research.get("hedgeFundSignal"),
                    "hedge_fund_score": research.get("rawHedgeFundsScore"),
                    "insider_signal": research.get("insiderSignal"),
                    "insider_score": research.get("rawInsiderScore"),
                    "news_sentiment_signal": research.get("newsSentiment"),
                    "news_sentiment_score": research.get("rawNewsSentiment"),
                    "top_investor_signal": research.get("bestInvestorSentiment"),
                    "top_investor_score": research.get("rawBestInvestorScore"),
                    "blogger_signal": research.get("bloggerConsensus"),
                }
            )

        return etf_results

    def fetch_etf_holdings(
        self,
        etf_ticker: str,
        total_holdings: int,
        *,
        page_size: int = 10,
        sleep_seconds: float = 0.5,
    ) -> list[JsonDict]:
        """
        Fetch all holdings for a single ETF.
        """
        if not total_holdings:
            return []

        holdings = []
        pages = math.ceil(total_holdings / page_size)

        for page in range(1, pages + 1):
            if sleep_seconds:
                time.sleep(sleep_seconds)

            LOGGER.info("Fetching holdings page %s/%s for %s", page, pages, etf_ticker)
            response = self._request(
                "GET",
                f"/api/etfs/holdings/{etf_ticker}",
                params={
                    "sortBy": 26,
                    "sortDir": 2,
                    "page": page,
                    "country": "us",
                    "pagesize": page_size,
                },
            )

            for holding in response.get("etfHoldings", []):
                holding_data = holding.get("holdingData") or {}
                assets_data = holding.get("assetsData") or {}

                price_target = assets_data.get("priceTarget", 0)
                price_target_upside = assets_data.get("priceTargetUpside", 0)
                price = None
                if price_target and price_target_upside is not None:
                    denominator = 1 + (price_target_upside / 100)
                    price = price_target / denominator if denominator else None

                top_analyst = assets_data.get("bestAnalystConcensus") or {}
                hedge_fund = assets_data.get("hedgeFundSentimentData") or {}
                insider = assets_data.get("insiderSentimentData") or {}
                blogger = assets_data.get("bloggerSentimentData") or {}

                holdings.append(
                    {
                        "etf_ticker": etf_ticker,
                        "holding_ticker": holding_data.get("holdingTicker"),
                        "stock_name": holding_data.get("companyName"),
                        "weight": holding_data.get("weight"),
                        "price": price,
                        "holding_smart_score": holding_data.get("holdingSmartScore"),
                        "top_analyst_rating": top_analyst.get("consensus"),
                        "top_analyst_rating_id": top_analyst.get("consensusId"),
                        "top_analyst_price_target": assets_data.get("bestPriceTarget"),
                        "top_analyst_price_target_upside": assets_data.get("bestPriceTargetUpside"),
                        "hedge_fund_rating": hedge_fund.get("rating"),
                        "hedge_fund_rating_id": hedge_fund.get("ratingId"),
                        "hedge_fund_score": hedge_fund.get("score"),
                        "insider_rating": insider.get("rating"),
                        "insider_rating_id": insider.get("ratingId"),
                        "insider_score": insider.get("stockScore"),
                        "blogger_rating": blogger.get("rating"),
                        "blogger_rating_id": blogger.get("ratingId"),
                        "news_sentiment_score": assets_data.get("newsSentiment"),
                    }
                )

        return holdings

    def fetch_stock_technicals(self, tickers: Union[str, list[str]]) -> pd.DataFrame:
        """
        Fetch technical indicator data for one or more stock tickers.
        """
        if isinstance(tickers, str):
            tickers = [tickers]
        if not tickers:
            return pd.DataFrame()

        response = self._request(
            "GET",
            "/api/compare/stocks/",
            params={"tickers": ",".join(tickers)},
        )
        stock_data = []

        for stock in response.get("extraData", []):
            research = stock.get("research", {})
            technicals = stock.get("technicalIndicators") or {}
            stock_data.append(
                {
                    "ticker": stock.get("ticker"),
                    "one_month_gain": research.get("oneMonthGain"),
                    "three_months_gain": research.get("threeMonthsGain"),
                    "six_months_gain": research.get("sixMonthsGain"),
                    "ytd_gain": research.get("ytdGain"),
                    "volumeAvg10d": technicals.get("volumeAvg10d"),
                    "volumeAvg30d": technicals.get("volumeAvg30d"),
                    "volumeAvg90d": technicals.get("volumeAvg90d"),
                    "emA21d": technicals.get("emA21d"),
                    "emA50d": technicals.get("emA50d"),
                    "movingAvg21d": technicals.get("movingAvg21d"),
                    "movingAvg50d": technicals.get("movingAvg50d"),
                    "movingAvg200d": technicals.get("movingAvg200d"),
                }
            )

        return pd.DataFrame(stock_data)
