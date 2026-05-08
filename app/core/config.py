from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    database_url: str = Field(default="sqlite:///./custom_agents.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    llm_base_url: str = Field(default="https://api.openai.com/v1", alias="LLM_BASE_URL")
    llm_api_key: str = Field(alias="LLM_API_KEY")
    llm_default_model: str = Field(default="gpt-4.1-mini", alias="LLM_DEFAULT_MODEL")
    llm_timeout_seconds: float = Field(default=90.0, alias="LLM_TIMEOUT_SECONDS")
    llm_retry_attempts: int = Field(default=1, alias="LLM_RETRY_ATTEMPTS")
    comfyui_base_url: str = Field(default="http://127.0.0.1:8188", alias="COMFYUI_BASE_URL")
    output_dir: str = Field(default="./output", alias="OUTPUT_DIR")
    image_backend: str = Field(default="comfyui_remote", alias="IMAGE_BACKEND")
    third_party_image_base_url: str = Field(default="", alias="THIRD_PARTY_IMAGE_BASE_URL")
    third_party_image_api_key: str = Field(default="", alias="THIRD_PARTY_IMAGE_API_KEY")
    third_party_image_model: str = Field(default="", alias="THIRD_PARTY_IMAGE_MODEL")
    third_party_image_api_path: str = Field(default="/images/generations", alias="THIRD_PARTY_IMAGE_API_PATH")
    third_party_image_timeout_seconds: float = Field(default=180.0, alias="THIRD_PARTY_IMAGE_TIMEOUT_SECONDS")
    third_party_image_retry_attempts: int = Field(default=1, alias="THIRD_PARTY_IMAGE_RETRY_ATTEMPTS")
    feishu_notify_webhook_url: str = Field(default="", alias="FEISHU_NOTIFY_WEBHOOK_URL")
    feishu_encrypt_key: str = Field(default="", alias="FEISHU_ENCRYPT_KEY")
    feishu_app_id: str = Field(default="", alias="FEISHU_APP_ID")
    feishu_app_secret: str = Field(default="", alias="FEISHU_APP_SECRET")
    feishu_open_base_url: str = Field(default="https://open.feishu.cn/open-apis", alias="FEISHU_OPEN_BASE_URL")
    feishu_verification_token: str = Field(default="", alias="FEISHU_VERIFICATION_TOKEN")
    feishu_webhook_max_age_seconds: int = Field(default=300, alias="FEISHU_WEBHOOK_MAX_AGE_SECONDS")
    mobile_access_token: str = Field(default="", alias="MOBILE_ACCESS_TOKEN")
    mobile_session_max_age_seconds: int = Field(default=28800, alias="MOBILE_SESSION_MAX_AGE_SECONDS")
    codex_cli_command: str = Field(default="codex", alias="CODEX_CLI_COMMAND")
    codex_cli_model: str = Field(default="", alias="CODEX_CLI_MODEL")
    codex_cli_timeout_seconds: int = Field(default=180, alias="CODEX_CLI_TIMEOUT_SECONDS")
    codex_run_timeout_seconds: int = Field(default=300, alias="CODEX_RUN_TIMEOUT_SECONDS")
    chatgpt_web_base_url: str = Field(default="https://chatgpt.com/", alias="CHATGPT_WEB_BASE_URL")
    chatgpt_web_profile_dir: str = Field(
        default="./runtime/playwright/chatgpt_web_profile",
        alias="CHATGPT_WEB_PROFILE_DIR",
    )
    chatgpt_web_headless: bool = Field(default=True, alias="CHATGPT_WEB_HEADLESS")
    chatgpt_web_timeout_seconds: float = Field(default=180.0, alias="CHATGPT_WEB_TIMEOUT_SECONDS")
    chatgpt_web_browser_channel: str = Field(default="", alias="CHATGPT_WEB_BROWSER_CHANNEL")
    chatgpt_web_executable_path: str = Field(default="", alias="CHATGPT_WEB_EXECUTABLE_PATH")
    chatgpt_web_cdp_url: str = Field(default="", alias="CHATGPT_WEB_CDP_URL")
    chatgpt_web_image_prompt_suffix: str = Field(default="", alias="CHATGPT_WEB_IMAGE_PROMPT_SUFFIX")
    dreamina_cli_path: str = Field(default="C:\\Users\\91799\\bin\\dreamina.exe", alias="DREAMINA_CLI_PATH")
    dreamina_image_model_version: str = Field(default="5.0", alias="DREAMINA_IMAGE_MODEL_VERSION")
    dreamina_image_ratio: str = Field(default="16:9", alias="DREAMINA_IMAGE_RATIO")
    dreamina_image_resolution_type: str = Field(default="2k", alias="DREAMINA_IMAGE_RESOLUTION_TYPE")
    dreamina_image_poll_seconds: int = Field(default=120, alias="DREAMINA_IMAGE_POLL_SECONDS")
    dreamina_image_timeout_seconds: int = Field(default=180, alias="DREAMINA_IMAGE_TIMEOUT_SECONDS")
    dreamina_image_output_dir: str = Field(default="./output/dreamina/images", alias="DREAMINA_IMAGE_OUTPUT_DIR")
    dreamina_image_retry_attempts: int = Field(default=0, alias="DREAMINA_IMAGE_RETRY_ATTEMPTS")
    dreamina_video_model_version: str = Field(default="seedance2.0", alias="DREAMINA_VIDEO_MODEL_VERSION")
    dreamina_video_ratio: str = Field(default="16:9", alias="DREAMINA_VIDEO_RATIO")
    dreamina_video_duration: int = Field(default=5, alias="DREAMINA_VIDEO_DURATION")
    dreamina_video_resolution: str = Field(default="720p", alias="DREAMINA_VIDEO_RESOLUTION")
    dreamina_video_poll_seconds: int = Field(default=180, alias="DREAMINA_VIDEO_POLL_SECONDS")
    dreamina_video_timeout_seconds: int = Field(default=300, alias="DREAMINA_VIDEO_TIMEOUT_SECONDS")
    dreamina_video_output_dir: str = Field(default="./output/dreamina/videos", alias="DREAMINA_VIDEO_OUTPUT_DIR")
    dreamina_video_retry_attempts: int = Field(default=0, alias="DREAMINA_VIDEO_RETRY_ATTEMPTS")
    conversation_idle_timeout_seconds: int = Field(default=7200, alias="CONVERSATION_IDLE_TIMEOUT_SECONDS")
    conversation_compact_trigger_count: int = Field(default=20, alias="CONVERSATION_COMPACT_TRIGGER_COUNT")
    conversation_keep_recent_count: int = Field(default=12, alias="CONVERSATION_KEEP_RECENT_COUNT")
    conversation_retention_seconds: int = Field(default=604800, alias="CONVERSATION_RETENTION_SECONDS")
    conversation_cleanup_batch_size: int = Field(default=100, alias="CONVERSATION_CLEANUP_BATCH_SIZE")
    auto_enqueue_jobs: bool = Field(default=False, alias="AUTO_ENQUEUE_JOBS")
    queue_name: str = Field(default="custom-agents", alias="QUEUE_NAME")


def load_settings(allow_placeholder_llm_api_key=False, env_file=".env"):
    try:
        if env_file is None:
            return Settings(_env_file=None)
        return Settings(_env_file=env_file)
    except ValidationError as exc:
        if allow_placeholder_llm_api_key and "LLM_API_KEY" in str(exc):
            if env_file is None:
                return Settings(_env_file=None, LLM_API_KEY="placeholder-llm-api-key")
            return Settings(_env_file=env_file, LLM_API_KEY="placeholder-llm-api-key")
        raise
