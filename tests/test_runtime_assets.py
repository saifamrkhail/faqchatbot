from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_dockerfile_exists_with_uv_sync_command() -> None:
    dockerfile = PROJECT_ROOT / "Dockerfile"
    content = dockerfile.read_text(encoding="utf-8")

    assert dockerfile.exists()
    assert "uv sync --frozen --no-dev" in content
    assert "CMD [\"faqchatbot\", \"--tui\"]" in content


def test_docker_compose_wires_app_qdrant_and_ingest_services() -> None:
    compose = PROJECT_ROOT / "docker-compose.yml"
    content = compose.read_text(encoding="utf-8")

    assert compose.exists()
    assert "qdrant:" in content
    assert "app:" in content
    assert "ingest:" in content
    assert "FAQ_CHATBOT_QDRANT_URL: http://qdrant:6333" in content


def test_dockerignore_excludes_local_virtualenv() -> None:
    dockerignore = PROJECT_ROOT / ".dockerignore"
    content = dockerignore.read_text(encoding="utf-8")

    assert dockerignore.exists()
    assert ".venv" in content
