from app.core.config import load_settings
from app.workers.queue import create_queue


class JobDispatcher:
    def enqueue_job(self, job_id):
        raise NotImplementedError


class NoopJobDispatcher(JobDispatcher):
    def enqueue_job(self, job_id):
        return {"dispatch_status": "skipped", "queue_name": None}


class RQJobDispatcher(JobDispatcher):
    def __init__(self, redis_url, queue_name):
        self.redis_url = redis_url
        self.queue_name = queue_name

    def enqueue_job(self, job_id):
        queue = create_queue(self.redis_url, queue_name=self.queue_name)
        queue.enqueue("app.workers.jobs.run_configured_job", job_id)
        return {"dispatch_status": "enqueued", "queue_name": self.queue_name}


def build_job_dispatcher(settings=None):
    settings = settings or load_settings(allow_placeholder_llm_api_key=True)
    if settings.auto_enqueue_jobs:
        return RQJobDispatcher(redis_url=settings.redis_url, queue_name=settings.queue_name)
    return NoopJobDispatcher()
