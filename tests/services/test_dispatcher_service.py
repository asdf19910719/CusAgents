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
