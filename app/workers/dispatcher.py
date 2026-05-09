from datetime import timedelta

from redis import Redis

from app.core.config import load_settings
from app.workers.queue import create_queue


class JobDispatcher:
    def enqueue_job(self, job_id):
        raise NotImplementedError

    def enqueue_codex_run(self, run_id):
        raise NotImplementedError

    def enqueue_video_job(self, video_id):
        raise NotImplementedError

    def enqueue_video_poll(self, video_id, delay_seconds):
        raise NotImplementedError


class NoopJobDispatcher(JobDispatcher):
    def enqueue_job(self, job_id):
        return {"dispatch_status": "skipped", "queue_name": None}

    def enqueue_codex_run(self, run_id):
        return {"dispatch_status": "skipped", "queue_name": None}

    def enqueue_video_job(self, video_id):
        return {"dispatch_status": "skipped", "queue_name": None}

    def enqueue_video_poll(self, video_id, delay_seconds):
        return {"dispatch_status": "skipped", "queue_name": None}


class RQJobDispatcher(JobDispatcher):
    def __init__(self, redis_url, queue_name):
        self.redis_url = redis_url
        self.queue_name = queue_name

    def enqueue_job(self, job_id):
        queue = create_queue(self.redis_url, queue_name=self.queue_name)
        queue.enqueue("app.workers.jobs.run_configured_job", job_id)
        return {"dispatch_status": "enqueued", "queue_name": self.queue_name}

    def enqueue_codex_run(self, run_id):
        queue = create_queue(self.redis_url, queue_name=self.queue_name)
        queue.enqueue("app.workers.jobs.run_configured_codex_run", run_id)
        return {"dispatch_status": "enqueued", "queue_name": self.queue_name}

    def enqueue_video_job(self, video_id):
        queue = create_queue(self.redis_url, queue_name=self.queue_name)
        queue.enqueue("app.workers.video_jobs.run_configured_video_job", video_id, job_timeout=600)
        return {"dispatch_status": "enqueued", "queue_name": self.queue_name}

    def enqueue_video_poll(self, video_id, delay_seconds):
        queue = create_queue(self.redis_url, queue_name=self.queue_name)
        dedupe_key = "video-poll:{0}:{1}".format(self.queue_name, video_id)
        dedupe_ttl = max(int(delay_seconds), 1)
        redis_connection = getattr(queue, "connection", None) or Redis.from_url(self.redis_url)
        if not redis_connection.set(dedupe_key, "pending", nx=True, ex=dedupe_ttl):
            return {"dispatch_status": "scheduled", "queue_name": self.queue_name}
        try:
            job = queue.enqueue_in(
                timedelta(seconds=delay_seconds),
                "app.workers.video_jobs.poll_configured_video_job",
                video_id,
                job_timeout=600,
            )
        except Exception:
            redis_connection.delete(dedupe_key)
            raise
        redis_connection.set(dedupe_key, getattr(job, "id", "scheduled"), ex=dedupe_ttl)
        return {"dispatch_status": "enqueued", "queue_name": self.queue_name}


def build_job_dispatcher(settings=None):
    settings = settings or load_settings(allow_placeholder_llm_api_key=True)
    if settings.auto_enqueue_jobs:
        return RQJobDispatcher(redis_url=settings.redis_url, queue_name=settings.queue_name)
    return NoopJobDispatcher()
