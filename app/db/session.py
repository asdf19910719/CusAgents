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
    if "jobs" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("jobs")}
    if "image_backend" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE jobs ADD COLUMN image_backend VARCHAR(64) NOT NULL DEFAULT 'comfyui_remote'")
            )


default_settings = load_settings(allow_placeholder_llm_api_key=True)
engine = create_engine_from_settings(default_settings)
ensure_development_schema_compatibility(engine)
SessionLocal = create_session_factory(default_settings)
