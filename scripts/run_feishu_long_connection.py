import argparse

from _bootstrap import ensure_project_root_on_path


ensure_project_root_on_path()

from app.channels.feishu_long_connection import FeishuLongConnectionRunner, build_feishu_long_connection_handler
from app.core.config import load_settings
from app.core.logging import setup_logging
from app.db.session import SessionLocal


def main():
    parser = argparse.ArgumentParser(description="Run or validate the Feishu long connection client.")
    parser.add_argument("--check", action="store_true", help="Validate configuration and client assembly only")
    parser.add_argument(
        "--connect-check",
        action="store_true",
        help="Establish and close one real long-connection session for diagnostics",
    )
    args = parser.parse_args()

    setup_logging()
    settings = load_settings(allow_placeholder_llm_api_key=False)
    if not settings.feishu_app_id or not settings.feishu_app_secret:
        raise RuntimeError("FEISHU_APP_ID and FEISHU_APP_SECRET are required")
    handler = build_feishu_long_connection_handler(settings, SessionLocal)
    runner = FeishuLongConnectionRunner(settings=settings, handler=handler)
    if args.check:
        runner.build_client()
        print("feishu long connection configuration ok")
        return
    if args.connect_check:
        runner.connect_check()
        print("feishu long connection connect check ok")
        return
    runner.start()


if __name__ == "__main__":
    main()
