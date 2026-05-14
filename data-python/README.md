# FinAi Data Fetchers

KRX 종목/지수 데이터를 가져오는 4가지 방식을 정리한 모음.

## 파일 구성

| 파일 | 데이터 소스 | 인증키 | 특징 |
|---|---|---|---|
| `fetch_pykrx.py` | data.krx.co.kr 스크래핑 | 불필요 | 펀더멘털·투자자 매매까지 폭넓음 |
| `fetch_fdr.py` | 네이버·야후 등 멀티 | 불필요 | 국내+해외+환율+지수 통합 |
| `fetch_yfinance.py` | Yahoo Finance | 불필요 | 해외 종목·재무제표·배당 |
| `fetch_krx_openapi.py` | **openapi.krx.co.kr 공식** | **필수** | KRX 공식, 서비스별 활용신청 필요 |

## 설치

```bash
pip install -r requirements.txt
```

## KRX 공식 OpenAPI 사용 절차

1. `https://openapi.krx.co.kr` 회원가입
2. **인증키 신청** → 관리자 승인 (마이페이지에서 발급 확인)
3. **서비스별 활용신청** → 또 한 번 관리자 승인 ★ 이게 핵심
4. `.env` 파일 생성 후 키 입력
   ```bash
   cp .env.example .env
   # KRX_AUTH_KEY=발급키 입력
   ```
5. 실행
   ```bash
   python fetch_krx_openapi.py
   ```

> **인증키 발급 ≠ 사용 가능.** 각 API마다 별도 활용신청·승인이 필요합니다. 신청 안 된 서비스 호출 시 401.

## 분석 목적별 KRX 서비스 신청 가이드

기본 종목 OHLCV 분석에 필요한 최소 세트:

| 카테고리 | 서비스 | 엔드포인트 |
|---|---|---|
| 주식 | 유가증권 일별매매정보 | `/sto/stk_bydd_trd` |
| 주식 | 코스닥 일별매매정보 | `/sto/ksq_bydd_trd` |
| 주식 | 유가증권 종목기본정보 | `/sto/stk_isu_base_info` |
| 주식 | 코스닥 종목기본정보 | `/sto/ksq_isu_base_info` |
| 지수 | KOSPI 시리즈 일별시세정보 | `/idx/krx_dd_trd` |

선택 추가:

| 목적 | 서비스 |
|---|---|
| 코스닥 지수도 함께 | KOSDAQ 시리즈 일별시세정보 |
| 외국인/기관 수급 | 투자자별 거래실적 |
| ETF 분석 | ETF 일별매매정보 |
| 파생·채권·ESG | 해당 카테고리에서 개별 신청 |

## 코드 핵심 함수 (fetch_krx_openapi.py)

```python
# 특정 일자 전 종목 스냅샷
get_kospi_daily("20260102")
get_kosdaq_daily("20260102")
get_krx_index_daily("20260102")

# 종목코드 하나만 필터
get_stock_by_ticker("20260102", "005930", market="KOSPI")

# 기간 시계열 (내부적으로 일자별 루프)
get_stock_range_by_ticker("005930", "20260501", "20260515", market="KOSPI")
fetch_range(get_krx_index_daily, "20260501", "20260515")

# 인증 검증
verify_auth()
```

## 출력 경로

`fetch_krx_openapi.py` 실행 결과는 다음 위치에 저장됩니다.

```
output/{TICKER}_{START}_{END}_{YYYYMMDD_HHMMSS}.csv
```

- 인코딩: `utf-8-sig` (엑셀에서 한글 호환)
- 디렉토리 자동 생성

## 라이브러리 선택 가이드

| 상황 | 권장 |
|---|---|
| 한 종목 긴 시계열 (백테스트) | `pykrx` (단일 호출로 기간 조회) |
| 특정 일자 시장 전체 스냅샷 | `fetch_krx_openapi` |
| 해외 종목·환율 함께 | `fetch_fdr` 또는 `fetch_yfinance` |
| 공식 데이터·재현성 중요 | `fetch_krx_openapi` |
| 빠른 프로토타이핑 | `fetch_fdr` |

## 주의사항

- KRX OpenAPI는 `http://`만 지원 (HTTPS 미제공)
- KRX OpenAPI는 키당 일일 호출 한도 있음
- `pykrx`는 스크래핑 기반이라 잦은 호출 시 차단 위험 → `time.sleep` 권장
- `yfinance`로 국내 종목 조회 시 `005930.KS`처럼 접미사 필요
- 일별 데이터는 장 마감(15:30 KST) 이후 갱신됨 — 당일 조회는 늦은 오후 이후

## 환경

- Python 3.10+
- 작성일: 2026-05-14
