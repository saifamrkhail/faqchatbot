#!/usr/bin/env bash

set -euo pipefail

OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
REQUIRED_MODELS=(
  "qwen3.5:9b"
  "nomic-embed-text-v2-moe"
)

if ! command -v ollama >/dev/null 2>&1; then
  echo "ollama CLI not found. Install Ollama on the host machine first." >&2
  exit 1
fi

if ! OLLAMA_HOST="$OLLAMA_HOST" ollama list >/dev/null 2>&1; then
  echo "Cannot reach host Ollama at $OLLAMA_HOST." >&2
  echo "Start Ollama on the host before running this script." >&2
  echo "If Docker cannot reach host Ollama on Linux, expose Ollama on 0.0.0.0:11434." >&2
  exit 1
fi

echo "Pulling required models from host Ollama at $OLLAMA_HOST"

for model in "${REQUIRED_MODELS[@]}"; do
  echo "  - $model"
  OLLAMA_HOST="$OLLAMA_HOST" ollama pull "$model"
done

echo
echo "Host Ollama models available:"
OLLAMA_HOST="$OLLAMA_HOST" ollama list
