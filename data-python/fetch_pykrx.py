"""
pykrx로 KRX 종목 데이터 가져오기

설치: pip install pykrx
"""

from pykrx import stock
import pandas as pd


def fetch_ohlcv(ticker: str, start: str, end: str) -> pd.DataFrame:
    """일별 시고저종 + 거래량/거래대금"""
    return stock.get_market_ohlcv(start, end, ticker)


def fetch_fundamental(ticker: str, start: str, end: str) -> pd.DataFrame:
    """BPS, PER, PBR, EPS, DIV, DPS"""
    return stock.get_market_fundamental(start, end, ticker)


def fetch_market_cap(ticker: str, start: str, end: str) -> pd.DataFrame:
    """시가총액, 상장주식수"""
    return stock.get_market_cap(start, end, ticker)


def fetch_trading_value_by_investor(ticker: str, start: str, end: str) -> pd.DataFrame:
    """투자자별 순매수 (외국인/기관/개인 등)"""
    return stock.get_market_trading_value_by_date(start, end, ticker)


def get_ticker_name(ticker: str) -> str:
    return stock.get_market_ticker_name(ticker)


if __name__ == "__main__":
    TICKER = "005930"  # 삼성전자
    START = "20240101"
    END = "20241231"

    print(f"[{TICKER}] {get_ticker_name(TICKER)}\n")

    ohlcv = fetch_ohlcv(TICKER, START, END)
    print("== OHLCV ==")
    print(ohlcv.tail(), "\n")

    fund = fetch_fundamental(TICKER, START, END)
    print("== Fundamental ==")
    print(fund.tail(), "\n")

    cap = fetch_market_cap(TICKER, START, END)
    print("== Market Cap ==")
    print(cap.tail(), "\n")

    flow = fetch_trading_value_by_investor(TICKER, START, END)
    print("== Investor Flow ==")
    print(flow.tail())
