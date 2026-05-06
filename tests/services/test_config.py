import pytest
from pydantic import ValidationError

from app.core.config import Settings, load_settings


def clear_settings_env(monkeypatch):
    keys = (
        "APP_ENV",
        "DATABASE_URL",
        "REDIS_URL",
        "LLM_BASE_URL",
        "LLM_API_KEY",
        "LLM_DEFAULT_MODEL",
        "COMFYUI_BASE_URL",
        "OUTPUT_DIR",
        "FEISHU_NOTIFY_WEBHOOK_URL",
        "FEISHU_VERIFICATION_TOKEN",
    )
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def test_settings_load_defaults_when_required_values_present(monkeypatch):
    clear_settings_env(monkeypatch)
    monkeypatch.setenv("LLM_API_KEY", "test-key")

    settings = Settings(_env_file=None)

    assert settings.app_env == "development"
    assert settings.database_url == "sqlite:///./custom_agents.db"
    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.llm_base_url == "https://api.openai.com/v1"
    assert settings.llm_api_key == "test-key"
    assert settings.llm_default_model == "gpt-4.1-mini"
    assert settings.comfyui_base_url == "http://127.0.0.1:8188"
    assert settings.output_dir == "./output"
    assert settings.third_party_image_api_path == "/images/generations"
    assert settings.feishu_notify_webhook_url == ""
    assert settings.feishu_verification_token == ""


def test_settings_require_llm_api_key(monkeypatch):
    clear_settings_env(monkeypatch)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert "LLM_API_KEY" in str(exc_info.value)


def test_settings_accept_sqlite_and_postgresql_urls(monkeypatch):
    clear_settings_env(monkeypatch)
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/custom_agents")

    postgres_settings = Settings(_env_file=None)

    assert postgres_settings.database_url == "postgresql://user:pass@localhost:5432/custom_agents"

    monkeypatch.setenv("DATABASE_URL", "sqlite:///./custom_agents.db")

    sqlite_settings = Settings(_env_file=None)

    assert sqlite_settings.database_url == "sqlite:///./custom_agents.db"


def test_load_settings_can_use_placeholder_key_when_explicitly_allowed(monkeypatch):
    clear_settings_env(monkeypatch)

    settings = load_settings(allow_placeholder_llm_api_key=True, env_file=None)

    assert settings.llm_api_key == "placeholder-llm-api-key"
