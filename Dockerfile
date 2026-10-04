# ===== Phase 1：（只用來裝套件，不會出現在最後的映像裡）=====
FROM python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 AS builder

# 從 uv 官方映像借用 uv 執行檔（同樣用 digest 鎖定）
COPY --from=ghcr.io/astral-sh/uv:0.12.19@sha256:04d046b13e60d6bcec73cbc5e1cad25d680dea90c8573340950a0ac2d1aef424 /uv /bin/uv

# 不准 uv 自己下載別的 Python；套件用複製的方式安裝
ENV UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy

WORKDIR /app

# 只複製兩個清單檔，照 uv.lock 安裝；--no-dev 不裝 pytest 等測試工具
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project


# ===== Phase 2：（真正要執行的映像）=====
FROM python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016

# 建立一般使用者，不用 root 執行
RUN useradd --uid 10001 --no-create-home appuser

WORKDIR /app

# 從 Phase 1 只拿裝好的套件；uv 本身不會帶過來
COPY --from=builder /app/.venv /app/.venv

# 複製程式碼
COPY app ./app

# 稽核紀錄的資料夾，交給一般使用者才寫得進去
RUN mkdir data && chown appuser:appuser data

# 讓系統找得到套件；日誌即時輸出；不產生暫存檔
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 從這一行開始，後面都用一般使用者的身分
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]