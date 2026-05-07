from app.workers import runner


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
