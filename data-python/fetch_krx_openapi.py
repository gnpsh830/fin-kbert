"""
KRX 공식 OpenAPI 클라이언트

발급: https://openapi.krx.co.kr → 회원가입 후 인증키 발급
인증: 모든 요청 헤더에 AUTH_KEY 포함

설치: pip install requests python-dotenv pandas

.env 파일에 다음을 설정:
    KRX_AUTH_KEY=발급받은_키
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta
from typing import Any, Callable

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

KRX_AUTH_KEY = os.getenv("KRX_AUTH_KEY")
if not KRX_AUTH_KEY:
    raise RuntimeError(
        "KRX_AUTH_KEY가 설정되지 않았습니다. .env 파일에 KRX_AUTH_KEY=... 를 추가하세요."
    )

BASE_URL = "http://data-dbg.krx.co.kr/svc/apis"


def _request(path: str, params: dict[str, Any]) -> pd.DataFrame:
    """KRX OpenAPI 공통 호출. 응답의 OutBlock_1을 DataFrame으로 반환."""
    headers = {"AUTH_KEY": KRX_AUTH_KEY}
    resp = requests.get(f"{BASE_URL}{path}", headers=headers, params=params, timeout=10)

    if resp.status_code != 200:
        # KRX는 본문에 한글 에러 메시지를 담아주므로 그대로 출력
        try:
            body = resp.json()
        except ValueError:
            body = resp.text[:500]
        raise requests.HTTPError(
            f"{resp.status_code} for {resp.url}\n  응답: {body}"
        )

    data = resp.json()
    rows = data.get("OutBlock_1", [])
    return pd.DataFrame(rows)


def verify_auth() -> None:
    """인증키가 유효한지 가벼운 호출로 확인."""
    masked = (
        KRX_AUTH_KEY[:4] + "*" * (len(KRX_AUTH_KEY) - 8) + KRX_AUTH_KEY[-4:]
        if len(KRX_AUTH_KEY) >= 8
        else "***"
    )
    print(f"로드된 키: {masked}  (길이={len(KRX_AUTH_KEY)})")
    print(f"엔드포인트: {BASE_URL}")
    # 과거 평일 하나로 테스트 (휴장일이면 빈 응답이라도 200이 떨어짐)
    try:
        df = get_kospi_daily("20240102")
        print(f"인증 OK — KOSPI 20240102 응답 {len(df)}건")
    except requests.HTTPError as e:
        print(f"인증 실패: {e}")


# ───── 주식 ─────

def get_kospi_daily(base_date: str) -> pd.DataFrame:
    """유가증권 일별매매정보 (전 종목, 특정 일자)
    base_date: YYYYMMDD
    """
    return _request("/sto/stk_bydd_trd", {"basDd": base_date})


def get_kosdaq_daily(base_date: str) -> pd.DataFrame:
    """코스닥 일별매매정보 (전 종목, 특정 일자)"""
    return _request("/sto/ksq_bydd_trd", {"basDd": base_date})


def get_konex_daily(base_date: str) -> pd.DataFrame:
    """코넥스 일별매매정보"""
    return _request("/sto/knx_bydd_trd", {"basDd": base_date})


def get_stock_base_info(base_date: str) -> pd.DataFrame:
    """유가증권 종목기본정보 (상장회사, 종목코드, 표준코드 등)"""
    return _request("/sto/stk_isu_base_info", {"basDd": base_date})


# ───── 지수 ─────

def get_krx_index_daily(base_date: str) -> pd.DataFrame:
    """KRX 시리즈 일별시세 (KOSPI, KOSDAQ 등 지수)"""
    return _request("/idx/krx_dd_trd", {"basDd": base_date})


# ───── 채권 ─────

def get_kts_bond_daily(base_date: str) -> pd.DataFrame:
    """국채 일별매매정보"""
    return _request("/bnd/kts_bydd_trd", {"basDd": base_date})


# ───── 유틸: 특정 종목코드만 필터 ─────

def get_stock_by_ticker(base_date: str, ticker: str, market: str = "KOSPI") -> pd.DataFrame:
    """전체 데이터를 받아온 후 특정 종목코드만 필터링.
    market: KOSPI | KOSDAQ | KONEX
    """
    fetchers = {
        "KOSPI": get_kospi_daily,
        "KOSDAQ": get_kosdaq_daily,
        "KONEX": get_konex_daily,
    }
    df = fetchers[market.upper()](base_date)
    if df.empty:
        return df
    return df[df["ISU_CD"] == ticker]


def fetch_range(
    fetcher: Callable[[str], pd.DataFrame],
    start: str,
    end: str,
    sleep: float = 0.2,
    skip_weekend: bool = True,
) -> pd.DataFrame:
    """기간 조회 헬퍼: start ~ end (YYYYMMDD, 양끝 포함) 사이를 하루씩 호출.
    - fetcher: get_kospi_daily 같이 basDd 하나만 받는 함수
    - skip_weekend: True면 토/일 스킵 (공휴일은 빈 응답으로 자동 처리됨)
    - sleep: 호출 간 대기(초). 차단 방지용.
    """
    start_dt = datetime.strptime(start, "%Y%m%d")
    end_dt = datetime.strptime(end, "%Y%m%d")

    frames: list[pd.DataFrame] = []
    cur = start_dt
    while cur <= end_dt:
        if skip_weekend and cur.weekday() >= 5:  # 5=토, 6=일
            cur += timedelta(days=1)
            continue
        day = cur.strftime("%Y%m%d")
        try:
            df = fetcher(day)
            if not df.empty:
                df = df.copy()
                df["BAS_DD"] = day
                frames.append(df)
                print(f"  [{day}] {len(df)}건")
            else:
                print(f"  [{day}] 데이터 없음 (휴장일 추정)")
        except requests.HTTPError as e:
            print(f"  [{day}] 오류: {e}")
        cur += timedelta(days=1)
        time.sleep(sleep)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def get_stock_range_by_ticker(
    ticker: str, start: str, end: str, market: str = "KOSPI"
) -> pd.DataFrame:
    """특정 종목의 기간 시계열."""
    fetchers = {
        "KOSPI": get_kospi_daily,
        "KOSDAQ": get_kosdaq_daily,
        "KONEX": get_konex_daily,
    }
    df = fetch_range(fetchers[market.upper()], start, end)
    if df.empty:
        return df
    return df[df["ISU_CD"] == ticker].reset_index(drop=True)


# 주식 일별매매정보(stk_bydd_trd / ksq_bydd_trd) 응답 컬럼의 한글 매핑.
# 초보자가 결과를 바로 이해할 수 있도록 CSV 저장 전에 컬럼명을 한글로 변환합니다.
STOCK_DAILY_COLUMN_KR: dict[str, str] = {
    "BAS_DD": "기준일자",
    "ISU_CD": "종목코드",
    "ISU_NM": "종목명",
    "MKT_NM": "시장구분",
    "SECT_TP_NM": "업종구분",
    "TDD_CLSPRC": "종가",
    "CMPPREVDD_PRC": "전일대비",
    "FLUC_RT": "등락률",
    "TDD_OPNPRC": "시가",
    "TDD_HGPRC": "고가",
    "TDD_LWPRC": "저가",
    "ACC_TRDVOL": "거래량",
    "ACC_TRDVAL": "거래대금",
    "MKTCAP": "시가총액",
    "LIST_SHRS": "상장주식수",
}


if __name__ == "__main__":
    START = "20260501"
    END = "20260515"
    TICKER = "005930"
    MARKET = "KOSPI"

    print(f"== {TICKER} {START} ~ {END} ==")
    df = get_stock_range_by_ticker(TICKER, START, END, market=MARKET)

    if df.empty:
        print("\n조회된 데이터가 없습니다.")
    else:
        # 컬럼명을 한글로 변환 (매핑에 없는 컬럼은 원본 유지)
        df = df.rename(columns=STOCK_DAILY_COLUMN_KR)
        print(df)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{TICKER}_{START}_{END}_{timestamp}.csv")
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"\n저장 완료: {out_path}")
