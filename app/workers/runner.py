import os

from rq import SimpleWorker, Worker

from app.core.config import load_settings
from app.core.logging import setup_logging
from app.workers.queue import create_queue


def build_worker(queue, platform_name=None, worker_cls=Worker, simple_worker_cls=SimpleWorker):
    platform_name = platform_name or os.name
    selected_cls = simple_worker_cls if platform_name == "nt" else worker_cls
    return selected_cls([queue], connection=queue.connection)


def run_worker():
    setup_logging()
    settings = load_settings(allow_placeholder_llm_api_key=True)
    queue = create_queue(settings.redis_url)
    worker = build_worker(queue)
    worker.work()
