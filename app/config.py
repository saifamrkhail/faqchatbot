"""Central application configuration."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path
from typing import Mapping

ENV_PREFIX = "FAQ_CHATBOT_"
_VALID_LOG_LEVELS = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_APP_NAME = "faqchatbot"
DEFAULT_ENVIRONMENT = "development"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_DEBUG = False
DEFAULT_FAQ_DATA_PATH = "data/faq.json"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_GENERATE_MODEL = "qwen3:8b"
DEFAULT_OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 30.0
DEFAULT_OLLAMA_GENERATE_TEMPERATURE = 0.1
DEFAULT_OLLAMA_GENERATE_MAX_TOKENS = 160
DEFAULT_QDRANT_URL = "http://localhost:6333"
DEFAULT_QDRANT_COLLECTION_NAME = "faq_entries"
DEFAULT_QDRANT_TIMEOUT_SECONDS = 30.0
DEFAULT_TOP_K = 3
DEFAULT_SCORE_THRESHOLD = 0.70
DEFAULT_FALLBACK_MESSAGE = "Leider konnte ich Ihre Frage nicht verstehen."
DEFAULT_MAX_QUESTION_CHARS = 500
DEFAULT_USE_STUB_UI_SERVICE = False


class SettingsError(ValueError):
    """Raised when the application settings are invalid."""


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Typed runtime settings loaded from environment variables."""

    app_name: str = DEFAULT_APP_NAME
    environment: str = DEFAULT_ENVIRONMENT
    log_level: str = DEFAULT_LOG_LEVEL
    debug: bool = DEFAULT_DEBUG
    faq_data_path: str = DEFAULT_FAQ_DATA_PATH
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL
    ollama_generate_model: str = DEFAULT_OLLAMA_GENERATE_MODEL
    ollama_embedding_model: str = DEFAULT_OLLAMA_EMBEDDING_MODEL
    ollama_timeout_seconds: float = DEFAULT_OLLAMA_TIMEOUT_SECONDS
    ollama_generate_temperature: float = DEFAULT_OLLAMA_GENERATE_TEMPERATURE
    ollama_generate_max_tokens: int = DEFAULT_OLLAMA_GENERATE_MAX_TOKENS
    qdrant_url: str = DEFAULT_QDRANT_URL
    qdrant_collection_name: str = DEFAULT_QDRANT_COLLECTION_NAME
    qdrant_timeout_seconds: float = DEFAULT_QDRANT_TIMEOUT_SECONDS
    top_k: int = DEFAULT_TOP_K
    score_threshold: float = DEFAULT_SCORE_THRESHOLD
    fallback_message: str = DEFAULT_FALLBACK_MESSAGE
    max_question_chars: int = DEFAULT_MAX_QUESTION_CHARS
    use_stub_ui_service: bool = DEFAULT_USE_STUB_UI_SERVICE

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "AppSettings":
        env = os.environ if environ is None else environ

        app_name = _get_string(env, "APP_NAME", DEFAULT_APP_NAME)
        environment = _get_string(env, "ENVIRONMENT", DEFAULT_ENVIRONMENT).lower()
        log_level = _parse_log_level(_get_string(env, "LOG_LEVEL", DEFAULT_LOG_LEVEL))
        debug = _parse_bool(_get_string(env, "DEBUG", str(DEFAULT_DEBUG)), "DEBUG")
        faq_data_path = _get_string(env, "FAQ_DATA_PATH", DEFAULT_FAQ_DATA_PATH)
        ollama_base_url = _get_string(env, "OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)
        ollama_generate_model = _get_string(
            env, "OLLAMA_GENERATE_MODEL", DEFAULT_OLLAMA_GENERATE_MODEL
        )
        ollama_embedding_model = _get_string(
            env, "OLLAMA_EMBEDDING_MODEL", DEFAULT_OLLAMA_EMBEDDING_MODEL
        )
        ollama_timeout_seconds = _parse_float(
            _get_string(
                env,
                "OLLAMA_TIMEOUT_SECONDS",
                str(DEFAULT_OLLAMA_TIMEOUT_SECONDS),
            ),
            "OLLAMA_TIMEOUT_SECONDS",
            minimum=0.1,
            maximum=300.0,
        )
        ollama_generate_temperature = _parse_float(
            _get_string(
                env,
                "OLLAMA_GENERATE_TEMPERATURE",
                str(DEFAULT_OLLAMA_GENERATE_TEMPERATURE),
            ),
            "OLLAMA_GENERATE_TEMPERATURE",
            minimum=0.0,
            maximum=2.0,
        )
        ollama_generate_max_tokens = _parse_int(
            _get_string(
                env,
                "OLLAMA_GENERATE_MAX_TOKENS",
                str(DEFAULT_OLLAMA_GENERATE_MAX_TOKENS),
            ),
            "OLLAMA_GENERATE_MAX_TOKENS",
            minimum=1,
        )
        qdrant_url = _get_string(env, "QDRANT_URL", DEFAULT_QDRANT_URL)
        qdrant_collection_name = _get_string(
            env, "QDRANT_COLLECTION_NAME", DEFAULT_QDRANT_COLLECTION_NAME
        )
        qdrant_timeout_seconds = _parse_float(
            _get_string(
                env,
                "QDRANT_TIMEOUT_SECONDS",
                str(DEFAULT_QDRANT_TIMEOUT_SECONDS),
            ),
            "QDRANT_TIMEOUT_SECONDS",
            minimum=0.1,
            maximum=300.0,
        )
        top_k = _parse_int(
            _get_string(env, "TOP_K", str(DEFAULT_TOP_K)),
            "TOP_K",
            minimum=1,
        )
        score_threshold = _parse_float(
            _get_string(env, "SCORE_THRESHOLD", str(DEFAULT_SCORE_THRESHOLD)),
            "SCORE_THRESHOLD",
            minimum=0.0,
            maximum=1.0,
        )
        fallback_message = _get_string(
            env, "FALLBACK_MESSAGE", DEFAULT_FALLBACK_MESSAGE
        )
        max_question_chars = _parse_int(
            _get_string(
                env,
                "MAX_QUESTION_CHARS",
                str(DEFAULT_MAX_QUESTION_CHARS),
            ),
            "MAX_QUESTION_CHARS",
            minimum=1,
        )
        use_stub_ui_service = _parse_bool(
            _get_string(
                env,
                "USE_STUB_UI_SERVICE",
                str(DEFAULT_USE_STUB_UI_SERVICE),
            ),
            "USE_STUB_UI_SERVICE",
        )

        if not environment:
            raise SettingsError("ENVIRONMENT must not be empty")

        return cls(
            app_name=app_name,
            environment=environment,
            log_level=log_level,
            debug=debug,
            faq_data_path=faq_data_path,
            ollama_base_url=ollama_base_url,
            ollama_generate_model=ollama_generate_model,
            ollama_embedding_model=ollama_embedding_model,
            ollama_timeout_seconds=ollama_timeout_seconds,
            ollama_generate_temperature=ollama_generate_temperature,
            ollama_generate_max_tokens=ollama_generate_max_tokens,
            qdrant_url=qdrant_url,
            qdrant_collection_name=qdrant_collection_name,
            qdrant_timeout_seconds=qdrant_timeout_seconds,
            top_k=top_k,
            score_threshold=score_threshold,
            fallback_message=fallback_message,
            max_question_chars=max_question_chars,
            use_stub_ui_service=use_stub_ui_service,
        )


def get_settings() -> AppSettings:
    """Return cached application settings."""

    return _load_settings()


def clear_settings_cache() -> None:
    """Clear the cached settings for tests or process reconfiguration."""

    _load_settings.cache_clear()


@lru_cache(maxsize=1)
def _load_settings() -> AppSettings:
    return AppSettings.from_env()


def resolve_project_path(path_value: str | Path) -> Path:
    """Resolve a project-relative path against the repository root."""

    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


def _get_string(env: Mapping[str, str], key: str, default: str) -> str:
    value = env.get(f"{ENV_PREFIX}{key}", default)
    stripped = value.strip()
    if not stripped:
        raise SettingsError(f"{key} must not be empty")
    return stripped


def _parse_bool(value: str, key: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise SettingsError(f"{key} must be a boolean value")


def _parse_int(value: str, key: str, *, minimum: int) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise SettingsError(f"{key} must be an integer") from exc

    if parsed < minimum:
        raise SettingsError(f"{key} must be >= {minimum}")
    return parsed


def _parse_float(value: str, key: str, *, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise SettingsError(f"{key} must be a float") from exc

    if parsed < minimum or parsed > maximum:
        raise SettingsError(f"{key} must be between {minimum} and {maximum}")
    return parsed


def _parse_log_level(value: str) -> str:
    normalized = value.upper()
    if normalized not in _VALID_LOG_LEVELS:
        supported = ", ".join(sorted(_VALID_LOG_LEVELS))
        raise SettingsError(f"LOG_LEVEL must be one of: {supported}")
    return normalized
