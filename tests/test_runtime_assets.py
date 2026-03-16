from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_dockerfile_exists_with_uv_sync_command() -> None:
    dockerfile = PROJECT_ROOT / "Dockerfile"
    content = dockerfile.read_text(encoding="utf-8")

    assert dockerfile.exists()
    assert "uv sync --frozen --no-dev" in content
    assert "CMD [\"faqchatbot\", \"--tui\"]" in content
    assert "localhost:11434" not in content


def test_docker_compose_wires_qdrant_and_host_ollama() -> None:
    compose = PROJECT_ROOT / "docker-compose.yml"
    content = compose.read_text(encoding="utf-8")

    assert compose.exists()
    assert "qdrant:" in content
    assert "app:" in content
    assert "ingest:" in content
    assert "image: qdrant/qdrant:v1.17.0" in content
    assert "\n  ollama:\n" not in content
    assert "\n  ollama-models:\n" not in content
    assert "extra_hosts:" in content
    assert "host.docker.internal:host-gateway" in content
    assert (
        "FAQ_CHATBOT_QDRANT_URL: "
        "${FAQ_CHATBOT_QDRANT_URL:-http://qdrant:6333}"
        in content
    )
    assert (
        "FAQ_CHATBOT_OLLAMA_BASE_URL: "
        "${FAQ_CHATBOT_OLLAMA_BASE_URL:-http://host.docker.internal:11434}"
        in content
    )
    assert "FAQ_CHATBOT_OLLAMA_ENABLE_THINKING: \"false\"" in content


def test_host_ollama_model_bootstrap_script_exists() -> None:
    script = PROJECT_ROOT / "scripts" / "pull_host_ollama_models.sh"
    content = script.read_text(encoding="utf-8")

    assert script.exists()
    assert 'OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"' in content
    assert '"qwen3.5:9b"' in content
    assert '"nomic-embed-text-v2-moe"' in content
    assert 'OLLAMA_HOST="$OLLAMA_HOST" ollama pull "$model"' in content


def test_dockerignore_excludes_local_virtualenv() -> None:
    dockerignore = PROJECT_ROOT / ".dockerignore"
    content = dockerignore.read_text(encoding="utf-8")

    assert dockerignore.exists()
    assert ".venv" in content
