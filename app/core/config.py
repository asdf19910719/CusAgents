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
    comfyui_base_url: str = Field(default="http://127.0.0.1:8188", alias="COMFYUI_BASE_URL")
    output_dir: str = Field(default="./output", alias="OUTPUT_DIR")
    image_backend: str = Field(default="comfyui_remote", alias="IMAGE_BACKEND")
    third_party_image_base_url: str = Field(default="", alias="THIRD_PARTY_IMAGE_BASE_URL")
    third_party_image_api_key: str = Field(default="", alias="THIRD_PARTY_IMAGE_API_KEY")
    third_party_image_model: str = Field(default="", alias="THIRD_PARTY_IMAGE_MODEL")
    third_party_image_api_path: str = Field(default="/images/generations", alias="THIRD_PARTY_IMAGE_API_PATH")
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
