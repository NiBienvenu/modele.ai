"""Central configuration of the platform.

Every setting comes from environment variables, usually written in the
`.env` file at the project root (copy `.env.example` to start).

Usage anywhere in the code:

    from config.settings import get_settings
    settings = get_settings()
    print(settings.model.name)

Settings are grouped by topic (model, generation, server, paths) so each
layer only reads the part it needs.
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from config.env import load_env_file

# Project root = parent of the `config/` folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------
# Small helpers to read typed values from the environment
# --------------------------------------------------------------------------
def _get_str(key: str, default: str) -> str:
    """An empty value (ex: `MODEL_PATH=`) means "use the default"."""
    return os.environ.get(key, "").strip() or default


def _get_optional_str(key: str) -> str | None:
    """Return None when the variable is missing or empty."""
    value = os.environ.get(key, "").strip()
    return value or None


def _get_int(key: str, default: int) -> int:
    return int(_get_str(key, str(default)))


def _get_optional_int(key: str) -> int | None:
    value = _get_optional_str(key)
    return int(value) if value is not None else None


def _get_float(key: str, default: float) -> float:
    return float(_get_str(key, str(default)))


def _get_bool(key: str, default: bool) -> bool:
    return _get_str(key, str(default)).lower() in {"1", "true", "yes", "on"}


def _get_path(key: str, default: str) -> Path:
    """Relative paths are resolved from the project root, so the app works from any folder."""
    path = Path(_get_str(key, default))
    return path if path.is_absolute() else PROJECT_ROOT / path


# --------------------------------------------------------------------------
# Settings groups
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class PathSettings:
    """Where the platform reads and writes its data (Docker volumes)."""

    models_dir: Path
    checkpoints_dir: Path
    datasets_dir: Path
    documents_dir: Path
    logs_dir: Path
    storage_dir: Path  # SQLite database of the conversations
    frontend_dir: Path  # Built web interface served by the backend (single image)

    @classmethod
    def from_env(cls) -> "PathSettings":
        return cls(
            models_dir=_get_path("MODELS_DIR", "models"),
            checkpoints_dir=_get_path("CHECKPOINTS_DIR", "checkpoints"),
            datasets_dir=_get_path("DATASETS_DIR", "datasets"),
            documents_dir=_get_path("DOCUMENTS_DIR", "documents"),
            logs_dir=_get_path("LOGS_DIR", "logs"),
            storage_dir=_get_path("STORAGE_DIR", "storage"),
            frontend_dir=_get_path("FRONTEND_DIR", "frontend/dist"),
        )


@dataclass(frozen=True)
class ModelSettings:
    """Which model to load and on which hardware."""

    name: str  # HuggingFace repo id, ex: TinyLlama/TinyLlama-1.1B-Chat-v1.0
    path: Path  # Local folder with the converted LitGPT weights
    tokenizer_path: Path | None  # Optional separate tokenizer folder
    device: str  # "auto", "cpu" or "cuda"
    devices: int  # Number of GPUs to use
    precision: str | None  # ex: "bf16-true", "16-true", "32-true" (None = automatic)
    quantize: str | None  # ex: "bnb.nf4" (needs bitsandbytes + GPU)
    auto_download: bool  # Download MODEL_NAME into MODEL_PATH when missing
    hf_token: str | None  # Token for private / gated HuggingFace models

    @classmethod
    def from_env(cls, paths: PathSettings) -> "ModelSettings":
        name = _get_str("MODEL_NAME", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        tokenizer = _get_optional_str("TOKENIZER_PATH")
        return cls(
            name=name,
            # By default the weights live in models/<org>/<name>, which is where `litgpt download` puts them
            path=_get_path("MODEL_PATH", str(paths.models_dir / name)),
            tokenizer_path=_get_path("TOKENIZER_PATH", "") if tokenizer else None,
            device=_get_str("DEVICE", "auto"),
            devices=_get_int("DEVICES", 1),
            precision=_get_optional_str("PRECISION"),
            quantize=_get_optional_str("QUANTIZE"),
            auto_download=_get_bool("AUTO_DOWNLOAD", True),
            hf_token=_get_optional_str("HF_TOKEN"),
        )


@dataclass(frozen=True)
class GenerationSettings:
    """Default sampling parameters used for every answer."""

    max_new_tokens: int
    temperature: float
    top_p: float
    top_k: int | None
    system_prompt: str | None

    @classmethod
    def from_env(cls) -> "GenerationSettings":
        return cls(
            max_new_tokens=_get_int("MAX_NEW_TOKENS", 256),
            temperature=_get_float("TEMPERATURE", 0.7),
            top_p=_get_float("TOP_P", 0.9),
            top_k=_get_optional_int("TOP_K"),
            system_prompt=_get_optional_str("SYSTEM_PROMPT"),
        )


@dataclass(frozen=True)
class ChatSettings:
    """Conversation options."""

    history_messages: int  # Previous messages sent to the model as context
    title_length: int  # Conversation title = start of the first question

    @classmethod
    def from_env(cls) -> "ChatSettings":
        return cls(
            history_messages=_get_int("CHAT_HISTORY_MESSAGES", 6),
            title_length=_get_int("CHAT_TITLE_LENGTH", 60),
        )


@dataclass(frozen=True)
class ServerSettings:
    """HTTP server options (used by the backend)."""

    host: str
    port: int
    cors_origins: list[str]
    max_prompt_length: int
    result_ttl_seconds: int  # How long finished answers stay available

    @classmethod
    def from_env(cls) -> "ServerSettings":
        origins = _get_str("CORS_ORIGINS", "http://localhost:5555")
        return cls(
            host=_get_str("HOST", "0.0.0.0"),
            port=_get_int("PORT", 4444),
            cors_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
            max_prompt_length=_get_int("MAX_PROMPT_LENGTH", 8000),
            result_ttl_seconds=_get_int("RESULT_TTL_SECONDS", 3600),
        )


@dataclass(frozen=True)
class Settings:
    """All settings of the platform, grouped by topic."""

    paths: PathSettings
    model: ModelSettings
    generation: GenerationSettings
    server: ServerSettings
    chat: ChatSettings
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        paths = PathSettings.from_env()
        return cls(
            paths=paths,
            model=ModelSettings.from_env(paths),
            generation=GenerationSettings.from_env(),
            server=ServerSettings.from_env(),
            chat=ChatSettings.from_env(),
            log_level=_get_str("LOG_LEVEL", "INFO").upper(),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load `.env` once and return the same Settings object everywhere."""
    load_env_file(Path(os.environ.get("ENV_FILE", PROJECT_ROOT / ".env")))
    return Settings.from_env()
