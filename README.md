# kr-finbert-mcp

snunlp/KR-FinBert-SC 한국어 금융 감성분석 MCP 서버.

## 설치

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## 실행

```bash
KR_FINBERT_MODEL=~/Study/FinAi/two/src/KR-FinBert-SC kr-finbert-mcp
```

## Docker

```bash
docker compose up -d --build
docker compose down
```

## 호출

```bash
curl -X POST http://127.0.0.1:8000/api/sentiment \
  -H "Content-Type: application/json" \
  -d '{"text":"삼성전자 3분기 영업이익 시장 기대치 상회"}'
```

MCP 클라이언트는 `http://127.0.0.1:8000/mcp`.
