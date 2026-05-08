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
        "LLM_TIMEOUT_SECONDS",
        "LLM_RETRY_ATTEMPTS",
        "THIRD_PARTY_IMAGE_TIMEOUT_SECONDS",
        "THIRD_PARTY_IMAGE_RETRY_ATTEMPTS",
        "COMFYUI_BASE_URL",
        "OUTPUT_DIR",
        "FEISHU_NOTIFY_WEBHOOK_URL",
        "FEISHU_ENCRYPT_KEY",
        "FEISHU_VERIFICATION_TOKEN",
        "FEISHU_WEBHOOK_MAX_AGE_SECONDS",
        "MOBILE_ACCESS_TOKEN",
        "MOBILE_SESSION_MAX_AGE_SECONDS",
        "CODEX_CLI_COMMAND",
        "CODEX_CLI_MODEL",
        "CODEX_CLI_TIMEOUT_SECONDS",
        "CODEX_RUN_TIMEOUT_SECONDS",
        "CHATGPT_WEB_BASE_URL",
        "CHATGPT_WEB_PROFILE_DIR",
        "CHATGPT_WEB_HEADLESS",
        "CHATGPT_WEB_TIMEOUT_SECONDS",
        "CHATGPT_WEB_BROWSER_CHANNEL",
        "CHATGPT_WEB_EXECUTABLE_PATH",
        "CHATGPT_WEB_CDP_URL",
        "CHATGPT_WEB_IMAGE_PROMPT_SUFFIX",
        "DREAMINA_CLI_PATH",
        "DREAMINA_IMAGE_MODEL_VERSION",
        "DREAMINA_IMAGE_RATIO",
        "DREAMINA_IMAGE_RESOLUTION_TYPE",
        "DREAMINA_IMAGE_POLL_SECONDS",
        "DREAMINA_IMAGE_TIMEOUT_SECONDS",
        "DREAMINA_IMAGE_OUTPUT_DIR",
        "DREAMINA_IMAGE_RETRY_ATTEMPTS",
        "DREAMINA_VIDEO_MODEL_VERSION",
        "DREAMINA_VIDEO_RATIO",
        "DREAMINA_VIDEO_DURATION",
        "DREAMINA_VIDEO_RESOLUTION",
        "DREAMINA_VIDEO_POLL_SECONDS",
        "DREAMINA_VIDEO_TIMEOUT_SECONDS",
        "DREAMINA_VIDEO_OUTPUT_DIR",
        "DREAMINA_VIDEO_RETRY_ATTEMPTS",
        "CONVERSATION_IDLE_TIMEOUT_SECONDS",
        "CONVERSATION_COMPACT_TRIGGER_COUNT",
        "CONVERSATION_KEEP_RECENT_COUNT",
        "CONVERSATION_RETENTION_SECONDS",
        "CONVERSATION_CLEANUP_BATCH_SIZE",
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
    assert settings.llm_timeout_seconds == 90.0
    assert settings.llm_retry_attempts == 1
    assert settings.comfyui_base_url == "http://127.0.0.1:8188"
    assert settings.output_dir == "./output"
    assert settings.third_party_image_api_path == "/images/generations"
    assert settings.third_party_image_timeout_seconds == 180.0
    assert settings.third_party_image_retry_attempts == 1
    assert settings.feishu_notify_webhook_url == ""
    assert settings.feishu_encrypt_key == ""
    assert settings.feishu_app_id == ""
    assert settings.feishu_app_secret == ""
    assert settings.feishu_open_base_url == "https://open.feishu.cn/open-apis"
    assert settings.feishu_verification_token == ""
    assert settings.feishu_webhook_max_age_seconds == 300
    assert settings.mobile_access_token == ""
    assert settings.mobile_session_max_age_seconds == 28800
    assert settings.codex_cli_command == "codex"
    assert settings.codex_cli_model == ""
    assert settings.codex_cli_timeout_seconds == 180
    assert settings.codex_run_timeout_seconds == 300
    assert settings.chatgpt_web_base_url == "https://chatgpt.com/"
    assert settings.chatgpt_web_profile_dir == "./runtime/playwright/chatgpt_web_profile"
    assert settings.chatgpt_web_headless is True
    assert settings.chatgpt_web_timeout_seconds == 180.0
    assert settings.chatgpt_web_browser_channel == ""
    assert settings.chatgpt_web_executable_path == ""
    assert settings.chatgpt_web_cdp_url == ""
    assert settings.chatgpt_web_image_prompt_suffix == ""
    assert settings.dreamina_cli_path == "C:\\Users\\91799\\bin\\dreamina.exe"
    assert settings.dreamina_image_model_version == "5.0"
    assert settings.dreamina_image_ratio == "16:9"
    assert settings.dreamina_image_resolution_type == "2k"
    assert settings.dreamina_image_poll_seconds == 120
    assert settings.dreamina_image_timeout_seconds == 180
    assert settings.dreamina_image_output_dir == "./output/dreamina/images"
    assert settings.dreamina_image_retry_attempts == 0
    assert settings.dreamina_video_model_version == "seedance2.0"
    assert settings.dreamina_video_ratio == "16:9"
    assert settings.dreamina_video_duration == 5
    assert settings.dreamina_video_resolution == "720p"
    assert settings.dreamina_video_poll_seconds == 180
    assert settings.dreamina_video_timeout_seconds == 300
    assert settings.dreamina_video_output_dir == "./output/dreamina/videos"
    assert settings.dreamina_video_retry_attempts == 0
    assert settings.conversation_idle_timeout_seconds == 7200
    assert settings.conversation_compact_trigger_count == 20
    assert settings.conversation_keep_recent_count == 12
    assert settings.conversation_retention_seconds == 604800
    assert settings.conversation_cleanup_batch_size == 100


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
