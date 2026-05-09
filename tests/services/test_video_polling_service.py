from app.db.models.video_job import VideoJob
from app.workers.video_jobs import poll_video_job, run_configured_video_job


class FakeRecoveryService:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def query_submit_id(self, submit_id, download_dir=None):
        self.calls.append({"submit_id": submit_id, "download_dir": download_dir})
        return self.result


class FakeDispatcher:
    def __init__(self):
        self.polls = []

    def enqueue_video_poll(self, video_id, delay_seconds):
        self.polls.append({"video_id": video_id, "delay_seconds": delay_seconds})
        return {"dispatch_status": "enqueued", "queue_name": "video-queue"}


class FakeSession:
    def __init__(self, job):
        self.job = job
        self.committed = 0
        self.closed = False

    def get(self, model, row_id):
        if model is VideoJob and self.job.id == row_id:
            return self.job
        return None

    def execute(self, *args, **kwargs):
        class EmptyResult:
            def scalars(self):
                return self

            def first(self):
                return None

        return EmptyResult()

    def add(self, value):
        return None

    def commit(self):
        self.committed += 1

    def close(self):
        self.closed = True


def make_video_job(status="querying"):
    job = VideoJob(
        id=777,
        request_id="req-777",
        prompt="video prompt",
        backend="dreamina_video_cli",
        mode="text2video",
        status=status,
        current_step="query_result",
        duration=4,
        ratio="16:9",
        video_resolution="720p",
        model_version="seedance2.0",
        reference_manifest_json={},
        submit_id="submit-777",
    )
    return job


def test_poll_video_job_requeues_when_still_querying():
    job = make_video_job()
    session = FakeSession(job)
    dispatcher = FakeDispatcher()
    recovery = FakeRecoveryService({"submit_id": "submit-777", "gen_status": "querying"})

    result = poll_video_job(
        777,
        session_factory=lambda: session,
        recovery_service=recovery,
        dispatcher=dispatcher,
        download_dir="./videos",
        poll_delay_seconds=45,
    )

    assert result["status"] == "querying"
    assert result["poll_dispatch_status"] == "enqueued"
    assert dispatcher.polls == [{"video_id": 777, "delay_seconds": 45}]
    assert recovery.calls == [{"submit_id": "submit-777", "download_dir": "./videos"}]
    assert session.closed is True


def test_poll_video_job_does_not_requeue_completed_job():
    job = make_video_job()
    session = FakeSession(job)
    dispatcher = FakeDispatcher()
    recovery = FakeRecoveryService({"submit_id": "submit-777", "gen_status": "success"})

    result = poll_video_job(
        777,
        session_factory=lambda: session,
        recovery_service=recovery,
        dispatcher=dispatcher,
        download_dir="./videos",
        poll_delay_seconds=45,
    )

    assert result["status"] == "completed"
    assert result["poll_dispatch_status"] is None
    assert dispatcher.polls == []


def test_run_configured_video_job_enqueues_first_poll_when_submit_is_querying(monkeypatch):
    job = make_video_job(status="pending")
    session = FakeSession(job)
    dispatcher = FakeDispatcher()

    class FakeVideoService:
        def run_video_job(self, session_arg, job_arg):
            job_arg.status = "querying"
            return job_arg

    monkeypatch.setattr("app.workers.video_jobs.SessionLocal", lambda: session)
    monkeypatch.setattr("app.workers.video_jobs.build_video_service", lambda settings: FakeVideoService())
    monkeypatch.setattr("app.workers.video_jobs.build_job_dispatcher", lambda settings: dispatcher)

    result = run_configured_video_job(777)

    assert result == {"video_id": 777, "status": "querying"}
    assert dispatcher.polls == [{"video_id": 777, "delay_seconds": 180}]
    assert session.closed is True
