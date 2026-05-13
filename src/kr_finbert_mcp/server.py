"""KR-FinBert-SC MCP server.

Exposes `analyze_sentiment(text)` as an MCP tool over Streamable HTTP.
"""

from __future__ import annotations

import logging
import os
from typing import TypedDict

import torch
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_NAME = os.environ.get("KR_FINBERT_MODEL", "snunlp/KR-FinBert-SC")
HOST = os.environ.get("MCP_HOST", "127.0.0.1")
PORT = int(os.environ.get("MCP_PORT", "8000"))
MAX_TOKENS = 512

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("kr_finbert_mcp")


def _pick_device() -> str:
    # 임시: CPU 고정. GPU/MPS 분기는 추후 복구.
    # if torch.cuda.is_available():
    #     return "cuda"
    # if torch.backends.mps.is_available():
    #     return "mps"
    return "cpu"


def _normalize_label(raw: str) -> str:
    s = raw.strip().lower()
    if "pos" in s or "긍정" in raw:
        return "positive"
    if "neg" in s or "부정" in raw:
        return "negative"
    if "neu" in s or "중립" in raw:
        return "neutral"
    return raw


class SentimentResult(TypedDict):
    label: str
    raw_label: str
    score: float
    truncated: bool
    model: str


class SentimentModel:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.device = _pick_device()
        log.info("Loading model %s on %s", model_name, self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()
        self.id2label = self.model.config.id2label
        log.info("id2label = %s", self.id2label)

    @torch.no_grad()
    def predict(self, text: str) -> SentimentResult:
        full_ids = self.tokenizer(text, return_tensors="pt", truncation=False).input_ids
        truncated = full_ids.size(1) > MAX_TOKENS

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_TOKENS,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        logits = self.model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0]
        idx = int(probs.argmax())
        raw_label = str(self.id2label[idx])

        return SentimentResult(
            label=_normalize_label(raw_label),
            raw_label=raw_label,
            score=float(probs[idx]),
            truncated=truncated,
            model=self.model_name,
        )


mcp = FastMCP("kr-finbert-mcp", host=HOST, port=PORT)
_model: SentimentModel | None = None


def _get_model() -> SentimentModel:
    global _model
    if _model is None:
        _model = SentimentModel(MODEL_NAME)
    return _model


@mcp.tool()
def analyze_sentiment(text: str) -> SentimentResult:
    """Classify Korean financial text sentiment as positive / neutral / negative.

    Uses snunlp/KR-FinBert-SC. Inputs longer than 512 tokens are truncated
    (`truncated=true` in the response). Optimized for Korean financial domain
    (news, comments); accuracy degrades on general-domain text.
    """
    if not text or not text.strip():
        raise ValueError("text must be a non-empty string")
    return _get_model().predict(text)


@mcp.custom_route("/api/sentiment", methods=["POST"])
async def analyze_sentiment_http(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "request body must be JSON"}, status_code=400)
    text = body.get("text") if isinstance(body, dict) else None
    if not isinstance(text, str) or not text.strip():
        return JSONResponse(
            {"error": "field 'text' must be a non-empty string"}, status_code=400
        )
    try:
        result = _get_model().predict(text)
    except Exception as e:
        log.exception("predict failed")
        return JSONResponse({"error": str(e)}, status_code=500)
    return JSONResponse(result)


def main() -> None:
    _get_model()
    log.info("Starting MCP server on http://%s:%d/mcp", HOST, PORT)
    log.info("REST endpoint available at http://%s:%d/api/sentiment", HOST, PORT)
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
