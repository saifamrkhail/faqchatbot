FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY scripts ./scripts
COPY data ./data
COPY .env.example ./.env.example

ENV PATH="/app/.venv/bin:$PATH"

CMD ["faqchatbot", "--tui"]
