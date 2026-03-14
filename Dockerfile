FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy project files first (all needed for uv sync)
COPY pyproject.toml uv.lock README.md ./
COPY app ./app
COPY scripts ./scripts
COPY data ./data
COPY .env.example ./.env.example

# Install dependencies
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Create a non-root user for the app
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Healthcheck to verify connectivity to services
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:11434/api/tags || exit 1

CMD ["faqchatbot", "--tui"]
