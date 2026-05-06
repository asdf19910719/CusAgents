from app.channels.feishu_long_connection import FeishuLongConnectionRunner, build_feishu_long_connection_handler
from app.core.config import load_settings
from app.core.logging import setup_logging
from app.db.session import SessionLocal


def main():
    setup_logging()
    settings = load_settings(allow_placeholder_llm_api_key=False)
    if not settings.feishu_app_id or not settings.feishu_app_secret:
        raise RuntimeError("FEISHU_APP_ID and FEISHU_APP_SECRET are required")
    handler = build_feishu_long_connection_handler(settings, SessionLocal)
    runner = FeishuLongConnectionRunner(settings=settings, handler=handler)
    runner.start()


if __name__ == "__main__":
    main()
