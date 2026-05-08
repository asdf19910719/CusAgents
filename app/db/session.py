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
                    "conversation_session_id INTEGER, "
                    "prompt_text TEXT NOT NULL, "
                    "resolved_prompt_text TEXT, "
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
    else:
        columns = {column["name"] for column in inspector.get_columns("codex_runs")}
        with engine.begin() as connection:
            if "conversation_session_id" not in columns:
                connection.execute(text("ALTER TABLE codex_runs ADD COLUMN conversation_session_id INTEGER"))
            if "resolved_prompt_text" not in columns:
                connection.execute(text("ALTER TABLE codex_runs ADD COLUMN resolved_prompt_text TEXT"))
    if "conversation_sessions" not in table_names:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE conversation_sessions ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "chat_id VARCHAR(128) NOT NULL, "
                    "status VARCHAR(32) NOT NULL, "
                    "started_at VARCHAR(32), "
                    "last_message_at VARCHAR(32), "
                    "closed_at VARCHAR(32), "
                    "close_reason VARCHAR(32), "
                    "created_at VARCHAR(32), "
                    "updated_at VARCHAR(32)"
                    ")"
                )
            )
    if "conversation_messages" not in table_names:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE conversation_messages ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "session_id INTEGER NOT NULL, "
                    "role VARCHAR(32) NOT NULL, "
                    "content_text TEXT NOT NULL, "
                    "source_type VARCHAR(32) NOT NULL, "
                    "source_run_id INTEGER, "
                    "is_compacted BOOLEAN NOT NULL DEFAULT 0, "
                    "created_at VARCHAR(32), "
                    "updated_at VARCHAR(32)"
                    ")"
                )
            )
    if "outbound_notifications" not in table_names:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE outbound_notifications ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "job_id INTEGER, "
                    "video_job_id INTEGER, "
                    "channel_type VARCHAR(32) NOT NULL, "
                    "target_id VARCHAR(128), "
                    "event_type VARCHAR(64) NOT NULL, "
                    "payload_json JSON NOT NULL, "
                    "status VARCHAR(32) NOT NULL, "
                    "error_message TEXT, "
                    "retry_count INTEGER NOT NULL DEFAULT 0, "
                    "created_at VARCHAR(32)"
                    ")"
                )
            )
    else:
        columns = {column["name"] for column in inspector.get_columns("outbound_notifications")}
        with engine.begin() as connection:
            if "video_job_id" not in columns:
                connection.execute(text("ALTER TABLE outbound_notifications ADD COLUMN video_job_id INTEGER"))
    if "video_jobs" not in table_names:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE video_jobs ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "request_id VARCHAR(64) NOT NULL UNIQUE, "
                    "topic VARCHAR(255), "
                    "prompt TEXT NOT NULL, "
                    "backend VARCHAR(64) NOT NULL DEFAULT 'dreamina_video_cli', "
                    "mode VARCHAR(32) NOT NULL DEFAULT 'text2video', "
                    "status VARCHAR(32) NOT NULL, "
                    "current_step VARCHAR(64) NOT NULL, "
                    "duration INTEGER NOT NULL DEFAULT 5, "
                    "ratio VARCHAR(16) NOT NULL DEFAULT '16:9', "
                    "video_resolution VARCHAR(16) NOT NULL DEFAULT '720p', "
                    "model_version VARCHAR(64) NOT NULL DEFAULT 'seedance2.0', "
                    "reference_manifest_json JSON NOT NULL DEFAULT '{}', "
                    "submit_id VARCHAR(128), "
                    "notification_target_id VARCHAR(128), "
                    "error_message TEXT, "
                    "created_at VARCHAR(32), "
                    "updated_at VARCHAR(32)"
                    ")"
                )
            )
    else:
        columns = {column["name"] for column in inspector.get_columns("video_jobs")}
        with engine.begin() as connection:
            if "reference_manifest_json" not in columns:
                connection.execute(text("ALTER TABLE video_jobs ADD COLUMN reference_manifest_json JSON NOT NULL DEFAULT '{}'"))
    if "video_assets" not in table_names:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE video_assets ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "video_job_id INTEGER NOT NULL, "
                    "file_path VARCHAR(255) NOT NULL, "
                    "preview_path VARCHAR(255), "
                    "thumbnail_path VARCHAR(255), "
                    "duration INTEGER NOT NULL, "
                    "ratio VARCHAR(16) NOT NULL, "
                    "video_resolution VARCHAR(16) NOT NULL, "
                    "status VARCHAR(32) NOT NULL, "
                    "metadata_json JSON NOT NULL, "
                    "created_at VARCHAR(32)"
                    ")"
                )
            )
    if "story_projects" not in table_names:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE story_projects ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "request_id VARCHAR(64) NOT NULL UNIQUE, "
                    "title VARCHAR(255) NOT NULL, "
                    "source_type VARCHAR(32) NOT NULL, "
                    "source_text TEXT NOT NULL, "
                    "style_prompt TEXT NOT NULL, "
                    "status VARCHAR(32) NOT NULL, "
                    "current_stage VARCHAR(64) NOT NULL, "
                    "notification_target_id VARCHAR(128), "
                    "error_message TEXT, "
                    "created_at VARCHAR(32), "
                    "updated_at VARCHAR(32)"
                    ")"
                )
            )
    if "story_reference_assets" not in table_names:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE story_reference_assets ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "project_id INTEGER NOT NULL, "
                    "asset_type VARCHAR(64) NOT NULL, "
                    "name VARCHAR(128) NOT NULL, "
                    "description TEXT NOT NULL, "
                    "prompt TEXT NOT NULL, "
                    "image_asset_id INTEGER, "
                    "file_path VARCHAR(255) NOT NULL, "
                    "status VARCHAR(32) NOT NULL, "
                    "metadata_json JSON NOT NULL, "
                    "created_at VARCHAR(32), "
                    "updated_at VARCHAR(32)"
                    ")"
                )
            )
    if "story_shots" not in table_names:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE story_shots ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "project_id INTEGER NOT NULL, "
                    "shot_index INTEGER NOT NULL, "
                    "title VARCHAR(255) NOT NULL, "
                    "script_text TEXT NOT NULL, "
                    "visual_description TEXT NOT NULL, "
                    "camera_motion TEXT NOT NULL, "
                    "character_names JSON NOT NULL, "
                    "scene_names JSON NOT NULL, "
                    "prop_names JSON NOT NULL, "
                    "duration INTEGER NOT NULL DEFAULT 5, "
                    "ratio VARCHAR(16) NOT NULL DEFAULT '16:9', "
                    "status VARCHAR(32) NOT NULL, "
                    "metadata_json JSON NOT NULL, "
                    "created_at VARCHAR(32), "
                    "updated_at VARCHAR(32)"
                    ")"
                )
            )
    if "story_shot_images" not in table_names:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE story_shot_images ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "project_id INTEGER NOT NULL, "
                    "shot_id INTEGER NOT NULL, "
                    "image_asset_id INTEGER, "
                    "file_path VARCHAR(255) NOT NULL, "
                    "image_type VARCHAR(32) NOT NULL, "
                    "prompt TEXT NOT NULL, "
                    "status VARCHAR(32) NOT NULL, "
                    "metadata_json JSON NOT NULL, "
                    "created_at VARCHAR(32), "
                    "updated_at VARCHAR(32)"
                    ")"
                )
            )
    if "story_shot_video_jobs" not in table_names:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE story_shot_video_jobs ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "project_id INTEGER NOT NULL, "
                    "shot_id INTEGER NOT NULL, "
                    "video_job_id INTEGER NOT NULL, "
                    "mode VARCHAR(32) NOT NULL, "
                    "submit_id VARCHAR(128), "
                    "status VARCHAR(32) NOT NULL, "
                    "reference_manifest_json JSON NOT NULL, "
                    "prompt TEXT NOT NULL, "
                    "metadata_json JSON NOT NULL, "
                    "started_at VARCHAR(32), "
                    "finished_at VARCHAR(32), "
                    "created_at VARCHAR(32), "
                    "updated_at VARCHAR(32)"
                    ")"
                )
            )
    if "story_pipeline_runs" not in table_names:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE story_pipeline_runs ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "project_id INTEGER NOT NULL, "
                    "run_type VARCHAR(32) NOT NULL, "
                    "status VARCHAR(32) NOT NULL, "
                    "checkpoint_json JSON NOT NULL, "
                    "error_message TEXT, "
                    "started_at VARCHAR(32), "
                    "finished_at VARCHAR(32), "
                    "created_at VARCHAR(32), "
                    "updated_at VARCHAR(32)"
                    ")"
                )
            )


default_settings = load_settings(allow_placeholder_llm_api_key=True)
engine = create_engine_from_settings(default_settings)
ensure_development_schema_compatibility(engine)
SessionLocal = create_session_factory(default_settings)
