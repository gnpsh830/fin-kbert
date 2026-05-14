"""
FinanceDataReader로 종목 데이터 가져오기 (국내/해외 모두 지원)

설치: pip install finance-datareader
"""

import FinanceDataReader as fdr
import pandas as pd


def fetch_ohlcv(ticker: str, start: str, end: str | None = None) -> pd.DataFrame:
    """
    일별 OHLCV + Change
    - 국내: "005930" (삼성전자), "035720" (카카오)
    - 해외: "AAPL", "TSLA", "NVDA"
    - 환율/지수: "USD/KRW", "KS11"(KOSPI), "KQ11"(KOSDAQ)
    """
    return fdr.DataReader(ticker, start, end)


def list_krx_tickers() -> pd.DataFrame:
    """KRX 전체 상장 종목"""
    return fdr.StockListing("KRX")


def list_us_tickers(market: str = "NASDAQ") -> pd.DataFrame:
    """미국 종목 리스트 (NASDAQ / NYSE / S&P500 / AMEX)"""
    return fdr.StockListing(market)


def search_by_name(name: str) -> pd.DataFrame:
    krx = list_krx_tickers()
    return krx[krx["Name"].str.contains(name, na=False)]


if __name__ == "__main__":
    # 국내 종목
    samsung = fetch_ohlcv("005930", "2024-01-01", "2024-12-31")
    print("== 삼성전자 ==")
    print(samsung.tail(), "\n")

    # 해외 종목
    apple = fetch_ohlcv("AAPL", "2024-01-01", "2024-12-31")
    print("== Apple ==")
    print(apple.tail(), "\n")

    # 환율
    usdkrw = fetch_ohlcv("USD/KRW", "2024-01-01", "2024-12-31")
    print("== USD/KRW ==")
    print(usdkrw.tail(), "\n")

    # 종목 검색
    print("== '카카오' 검색 ==")
    print(search_by_name("카카오"))
