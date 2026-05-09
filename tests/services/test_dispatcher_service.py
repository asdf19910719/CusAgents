from datetime import timedelta

from app.core.config import Settings
from app.workers.dispatcher import NoopJobDispatcher, RQJobDispatcher, build_job_dispatcher


def test_build_job_dispatcher_defaults_to_noop_when_auto_enqueue_disabled():
    dispatcher = build_job_dispatcher(
        Settings(
            LLM_API_KEY="test-key",
            AUTO_ENQUEUE_JOBS=False,
        )
    )

    assert isinstance(dispatcher, NoopJobDispatcher)


def test_build_job_dispatcher_uses_rq_when_auto_enqueue_enabled():
    dispatcher = build_job_dispatcher(
        Settings(
            LLM_API_KEY="test-key",
            AUTO_ENQUEUE_JOBS=True,
            QUEUE_NAME="real-queue",
            REDIS_URL="redis://localhost:6379/0",
        )
    )

    assert isinstance(dispatcher, RQJobDispatcher)
    assert dispatcher.queue_name == "real-queue"


def test_rq_dispatcher_sets_video_job_timeout(monkeypatch):
    calls = []

    class FakeQueue:
        def enqueue(self, target, job_id, **kwargs):
            calls.append({"target": target, "job_id": job_id, "kwargs": kwargs})

    monkeypatch.setattr("app.workers.dispatcher.create_queue", lambda redis_url, queue_name: FakeQueue())
    dispatcher = RQJobDispatcher(redis_url="redis://localhost:6379/0", queue_name="video-queue")

    result = dispatcher.enqueue_video_job(123)

    assert result == {"dispatch_status": "enqueued", "queue_name": "video-queue"}
    assert calls == [
        {
            "target": "app.workers.video_jobs.run_configured_video_job",
            "job_id": 123,
            "kwargs": {"job_timeout": 600},
        }
    ]


def test_rq_dispatcher_enqueues_video_poll_with_delay(monkeypatch):
    calls = []

    class FakeQueue:
        def __init__(self):
            self.connection = FakeRedis()

        def enqueue_in(self, delay, target, *args, **kwargs):
            calls.append({"delay": delay, "target": target, "args": args, "kwargs": kwargs})

    class FakeRedis:
        def set(self, key, value, nx=False, ex=None):
            return True

        def delete(self, key):
            return None

    monkeypatch.setattr("app.workers.dispatcher.create_queue", lambda redis_url, queue_name: FakeQueue())
    dispatcher = RQJobDispatcher(redis_url="redis://localhost:6379/0", queue_name="video-queue")

    result = dispatcher.enqueue_video_poll(456, delay_seconds=90)

    assert result == {"dispatch_status": "enqueued", "queue_name": "video-queue"}
    assert calls == [
        {
            "delay": timedelta(seconds=90),
            "target": "app.workers.video_jobs.poll_configured_video_job",
            "args": (456,),
            "kwargs": {"job_timeout": 600},
        }
    ]


def test_rq_dispatcher_deduplicates_video_poll_with_redis_key(monkeypatch):
    calls = []
    redis_values = {}

    class FakeQueue:
        def __init__(self):
            self.connection = FakeRedis()

        def enqueue_in(self, delay, target, *args, **kwargs):
            calls.append({"delay": delay, "target": target, "args": args, "kwargs": kwargs})

            class FakeJob:
                id = "generated-job-1"

            return FakeJob()

    class FakeRedis:
        def set(self, key, value, nx=False, ex=None):
            if nx and key in redis_values:
                return False
            redis_values[key] = {"value": value, "ex": ex}
            return True

        def delete(self, key):
            redis_values.pop(key, None)

    monkeypatch.setattr("app.workers.dispatcher.create_queue", lambda redis_url, queue_name: FakeQueue())
    dispatcher = RQJobDispatcher(redis_url="redis://localhost:6379/0", queue_name="video-queue")

    first = dispatcher.enqueue_video_poll(456, delay_seconds=90)
    second = dispatcher.enqueue_video_poll(456, delay_seconds=90)

    assert first == {"dispatch_status": "enqueued", "queue_name": "video-queue"}
    assert second == {"dispatch_status": "scheduled", "queue_name": "video-queue"}
    assert calls == [
        {
            "delay": timedelta(seconds=90),
            "target": "app.workers.video_jobs.poll_configured_video_job",
            "args": (456,),
            "kwargs": {"job_timeout": 600},
        }
    ]
    assert redis_values == {
        "video-poll:video-queue:456": {
            "value": "generated-job-1",
            "ex": 90,
        }
    }
