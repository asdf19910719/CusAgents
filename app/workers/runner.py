from rq import Worker

from app.core.config import load_settings
from app.core.logging import setup_logging
from app.workers.queue import create_queue


def run_worker():
    setup_logging()
    settings = load_settings(allow_placeholder_llm_api_key=True)
    queue = create_queue(settings.redis_url)
    worker = Worker([queue], connection=queue.connection)
    worker.work()
