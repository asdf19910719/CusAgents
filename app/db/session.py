from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.core.config import load_settings


def create_engine_from_settings(settings):
    return create_engine(settings.database_url, future=True)


def create_session_factory(settings):
    engine = create_engine_from_settings(settings)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def ensure_development_schema_compatibility(engine):
    if engine.dialect.name != "sqlite":
        return
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "jobs" in table_names:
        columns = {column["name"] for column in inspector.get_columns("jobs")}
        with engine.begin() as connection:
            if "image_backend" not in columns:
                connection.execute(
                    text("ALTER TABLE jobs ADD COLUMN image_backend VARCHAR(64) NOT NULL DEFAULT 'comfyui_remote'")
                )
            if "notification_target_id" not in columns:
                connection.execute(text("ALTER TABLE jobs ADD COLUMN notification_target_id VARCHAR(128)"))
    if "codex_runs" not in table_names:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE codex_runs ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "request_id VARCHAR(64) NOT NULL UNIQUE, "
                    "channel_type VARCHAR(32) NOT NULL, "
                    "sender_id VARCHAR(128) NOT NULL, "
                    "notification_target_id VARCHAR(128), "
                    "prompt_text TEXT NOT NULL, "
                    "status VARCHAR(32) NOT NULL, "
                    "result_text TEXT, "
                    "output_text_path VARCHAR(255), "
                    "image_paths_json TEXT, "
                    "error_message TEXT, "
                    "created_at VARCHAR(32), "
                    "updated_at VARCHAR(32)"
                    ")"
                )
            )


default_settings = load_settings(allow_placeholder_llm_api_key=True)
engine = create_engine_from_settings(default_settings)
ensure_development_schema_compatibility(engine)
SessionLocal = create_session_factory(default_settings)
