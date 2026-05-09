from rq.scheduler import RQScheduler

from app.core.config import load_settings
from app.core.logging import setup_logging
from app.workers.queue import create_queue


def build_scheduler(queue, scheduler_cls=RQScheduler):
    return scheduler_cls([queue.name], connection=queue.connection)


def run_scheduler():
    setup_logging()
    settings = load_settings(allow_placeholder_llm_api_key=True)
    queue = create_queue(settings.redis_url, queue_name=settings.queue_name)
    scheduler = build_scheduler(queue)
    scheduler.work()
