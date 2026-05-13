FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src

# CPU 전용 PyTorch로 이미지 크기 절약 (~2GB -> ~600MB).
# GPU(CUDA)가 필요하면 이 줄을 지우고 기본 인덱스로 설치하세요.
RUN pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.1" \
 && pip install .

ENV MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    KR_FINBERT_MODEL=/models/KR-FinBert-SC

EXPOSE 8000

CMD ["kr-finbert-mcp"]
