from app.workers import runner
from app.workers import scheduler


def test_build_worker_uses_simple_worker_on_windows():
    class FakeQueue:
        def __init__(self):
            self.connection = "fake-connection"

    queue = FakeQueue()

    class FakeSimpleWorker:
        def __init__(self, queues, connection=None):
            self.queues = queues
            self.connection = connection

    class FakeWorker:
        def __init__(self, queues, connection=None):
            self.queues = queues
            self.connection = connection

    worker = runner.build_worker(
        queue=queue,
        platform_name="nt",
        worker_cls=FakeWorker,
        simple_worker_cls=FakeSimpleWorker,
    )

    assert isinstance(worker, FakeSimpleWorker)
    assert worker.queues == [queue]
    assert worker.connection == "fake-connection"


def test_run_worker_uses_configured_queue_name(monkeypatch):
    calls = {}

    class FakeSettings:
        redis_url = "redis://localhost:6379/0"
        queue_name = "configured-queue"

    class FakeWorker:
        def work(self):
            calls["worked"] = True

    monkeypatch.setattr(runner, "setup_logging", lambda: None)
    monkeypatch.setattr(runner, "load_settings", lambda allow_placeholder_llm_api_key=False: FakeSettings())
    monkeypatch.setattr(
        runner,
        "create_queue",
        lambda redis_url, queue_name="custom-agents": calls.update(
            {"redis_url": redis_url, "queue_name": queue_name}
        )
        or "fake-queue",
    )
    monkeypatch.setattr(runner, "build_worker", lambda queue: FakeWorker())

    runner.run_worker()

    assert calls == {
        "redis_url": "redis://localhost:6379/0",
        "queue_name": "configured-queue",
        "worked": True,
    }


def test_run_scheduler_uses_configured_queue_name(monkeypatch):
    calls = {}

    class FakeSettings:
        redis_url = "redis://localhost:6379/0"
        queue_name = "scheduled-queue"

    class FakeScheduler:
        def work(self):
            calls["worked"] = True

    monkeypatch.setattr(scheduler, "setup_logging", lambda: None)
    monkeypatch.setattr(scheduler, "load_settings", lambda allow_placeholder_llm_api_key=False: FakeSettings())
    monkeypatch.setattr(
        scheduler,
        "create_queue",
        lambda redis_url, queue_name="custom-agents": calls.update(
            {"redis_url": redis_url, "queue_name": queue_name}
        )
        or "fake-queue",
    )
    monkeypatch.setattr(scheduler, "build_scheduler", lambda queue: FakeScheduler())

    scheduler.run_scheduler()

    assert calls == {
        "redis_url": "redis://localhost:6379/0",
        "queue_name": "scheduled-queue",
        "worked": True,
    }
