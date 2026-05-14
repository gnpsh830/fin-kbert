"""
yfinance로 종목 데이터 가져와서 CSV로 저장하기 (초보자용)

[yfinance란?]
야후 파이낸스(Yahoo Finance)의 무료 데이터를 파이썬에서 가져오는 라이브러리.
인증키 없이 바로 사용 가능하고, 국내·해외 종목·환율·지수를 모두 지원합니다.

[설치]
    pip install yfinance pandas

[국내 종목 표기 규칙]
    yfinance에서 국내 종목은 종목코드 뒤에 시장 접미사를 붙입니다.
        - KOSPI: 005930.KS    (삼성전자)
        - KOSDAQ: 035720.KQ   (예시)
        - 해외: AAPL, TSLA, NVDA  (접미사 없음)

[실행]
    python fetch_yfinance.py
"""

import os
from datetime import datetime

import yfinance as yf


# yfinance 일별 시세 응답 컬럼의 한글 매핑.
# Date는 컬럼이 아니라 DataFrame의 인덱스이므로 별도 처리합니다.
YF_OHLCV_COLUMN_KR: dict[str, str] = {
    "Open": "시가",
    "High": "고가",
    "Low": "저가",
    "Close": "종가",
    "Adj Close": "수정종가",
    "Volume": "거래량",
    "Dividends": "배당금",
    "Stock Splits": "액면분할",
}

# Date 인덱스의 한글 이름
YF_INDEX_NAME_KR: str = "날짜"


def main() -> None:
    # ─────────────────────────────────────────────
    # 1단계: 조회 조건 설정
    # ─────────────────────────────────────────────
    # 종목코드: 야후 파이낸스 표기 (국내는 .KS / .KQ 필수)
    TICKER = "005930.KS"  # 삼성전자

    # 시작일과 종료일 (형식: "YYYY-MM-DD")
    # ⚠ 중요: yfinance의 end는 "exclusive"입니다.
    #         즉, end="2026-05-16"이면 실제로는 5/15까지 포함됩니다.
    #         만약 5/15까지 보고 싶다면 END에 하루 더한 5/16을 넣어야 합니다.
    START = "2026-05-01"
    END = "2026-05-16"  # 실제 데이터는 5/15까지 포함

    print(f"[조회 시작] 종목: {TICKER}, 기간: {START} ~ {END}\n")

    # ─────────────────────────────────────────────
    # 2단계: yfinance로 일별 시세(OHLCV) 가져오기
    # ─────────────────────────────────────────────
    # yf.Ticker(...)      : 특정 종목에 대한 객체 생성
    # .history(...)       : 일별/분봉 시세 데이터를 DataFrame으로 반환
    #
    # 주요 파라미터:
    #   - start, end   : 조회 기간
    #   - interval     : 봉 단위 ("1d"=일봉, "1h"=시간봉, "5m"=5분봉 등)
    #                    분봉은 최근 60일 이내만 조회 가능
    #   - auto_adjust  : True면 배당/분할 반영된 수정주가 사용
    #                    False면 원본 가격 + Adj Close 컬럼 별도 제공
    ticker_obj = yf.Ticker(TICKER)
    df = ticker_obj.history(
        start=START,
        end=END,
        interval="1d",
        auto_adjust=False,
    )

    # ─────────────────────────────────────────────
    # 3단계: 결과 확인
    # ─────────────────────────────────────────────
    if df.empty:
        # 데이터가 비어있는 경우: 종목코드 오타, 미래 날짜, 휴장일만 포함된 경우 등
        print("⚠ 데이터가 없습니다. 다음을 확인하세요:")
        print("  - 종목코드 표기 (KOSPI는 .KS, KOSDAQ은 .KQ)")
        print("  - 날짜 범위가 너무 미래이거나 모두 휴장일인지")
        return

    print(f"[데이터 {len(df)}건 수신]")

    # ─────────────────────────────────────────────
    # 3.5단계: 컬럼명 한글로 변환
    # ─────────────────────────────────────────────
    # - 컬럼(Open/High/...): df.rename(columns=...)
    # - 인덱스(Date)는 컬럼이 아니므로 별도로 이름 변경
    df = df.rename(columns=YF_OHLCV_COLUMN_KR)
    df.index.name = YF_INDEX_NAME_KR

    print(df)  # 한글 헤더로 출력
    print()

    # ─────────────────────────────────────────────
    # 4단계: CSV로 저장 (실행 타임스탬프 포함 파일명)
    # ─────────────────────────────────────────────
    # 같은 종목을 여러 번 조회해도 파일이 덮어쓰이지 않도록
    # 파일명에 "실행 시각"을 포함시킵니다.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # 예: 20260514_073927

    # 저장 폴더: 현재 스크립트 위치 기준 output/ 디렉토리
    out_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)  # 폴더가 없으면 자동 생성

    # 파일명 구성: yf_{종목}_{시작}_{종료}_{타임스탬프}.csv
    s_tag = START.replace("-", "")
    e_tag = END.replace("-", "")
    filename = f"yf_{TICKER}_{s_tag}_{e_tag}_{timestamp}.csv"
    out_path = os.path.join(out_dir, filename)

    # to_csv 옵션 설명:
    #   - index=True (기본값): 날짜를 첫 컬럼으로 함께 저장
    #   - encoding="utf-8-sig": 엑셀에서 한글 깨짐 방지 (BOM 포함)
    df.to_csv(out_path, encoding="utf-8-sig")

    print(f"[저장 완료] {out_path}")


if __name__ == "__main__":
    # 이 파일을 직접 실행했을 때만 main()이 호출됨.
    # 다른 파일에서 import할 때는 실행되지 않음.
    main()
