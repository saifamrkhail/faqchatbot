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


def test_docker_compose_wires_bundled_runtime_services() -> None:
    compose = PROJECT_ROOT / "docker-compose.yml"
    content = compose.read_text(encoding="utf-8")

    assert compose.exists()
    assert "ollama:" in content
    assert "ollama-models:" in content
    assert "qdrant:" in content
    assert "app:" in content
    assert "ingest:" in content
    assert "image: ollama/ollama:0.18.0" in content
    assert "image: qdrant/qdrant:v1.17.0" in content
    assert "ollama pull qwen3.5:9b" in content
    assert "ollama pull nomic-embed-text-v2-moe" in content
    assert "condition: service_completed_successfully" in content
    assert "FAQ_CHATBOT_QDRANT_URL: http://qdrant:6333" in content
    assert "FAQ_CHATBOT_OLLAMA_BASE_URL: http://ollama:11434" in content
    assert "FAQ_CHATBOT_OLLAMA_ENABLE_THINKING: \"false\"" in content


def test_dockerignore_excludes_local_virtualenv() -> None:
    dockerignore = PROJECT_ROOT / ".dockerignore"
    content = dockerignore.read_text(encoding="utf-8")

    assert dockerignore.exists()
    assert ".venv" in content
