from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.commands.parser import parse_command_text
from app.commands.router import CommandRouter
from app.db.base import Base
from app.db.models.job import Job


class FakeDispatcher:
    def __init__(self):
        self.job_calls = []
        self.codex_calls = []

    def enqueue_job(self, job_id):
        self.job_calls.append(job_id)
        return {"dispatch_status": "enqueued", "queue_name": "test-queue"}

    def enqueue_codex_run(self, run_id):
        self.codex_calls.append(run_id)
        return {"dispatch_status": "enqueued", "queue_name": "test-queue"}


class FakeNotificationService:
    def __init__(self):
        self.calls = []

    def notify_job_event(self, session, job, event_type, message, target_id=None):
        self.calls.append(
            {
                "job_id": getattr(job, "id", None) if job is not None else None,
                "event_type": event_type,
                "message": message,
                "target_id": target_id,
            }
        )
        return None


def test_command_router_creates_codex_run_and_enqueues_it():
    from app.core.config import Settings
    from app.db.models.codex_run import CodexRun

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    dispatcher = FakeDispatcher()
    notifications = FakeNotificationService()
    router = CommandRouter(
        dispatcher=dispatcher,
        notification_service=notifications,
        settings=Settings(_env_file=None, LLM_API_KEY="test-key"),
    )
    command = parse_command_text(
        '/codex prompt="Summarize current blockers"',
        channel="feishu",
        sender_id="ou_test_user",
        chat_id="oc_test_chat",
    )

    with Session(engine) as session:
        result = router.handle(session, command)
        run = session.query(CodexRun).order_by(CodexRun.id.desc()).one()

        assert result.success is True
        assert result.command_name == "run_codex"
        assert result.payload["dispatch_status"] == "enqueued"
        assert result.payload["run_id"] == run.id
        assert run.prompt_text == "Summarize current blockers"
        assert run.notification_target_id == "oc_test_chat"
        assert dispatcher.codex_calls == [run.id]


def test_command_router_can_query_codex_run_status():
    from app.core.config import Settings
    from app.db.models.codex_run import CodexRun

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    router = CommandRouter(
        dispatcher=FakeDispatcher(),
        notification_service=FakeNotificationService(),
        settings=Settings(_env_file=None, LLM_API_KEY="test-key"),
    )

    with Session(engine) as session:
        run = CodexRun(
            request_id="codex-run-1",
            sender_id="ou_test_user",
            channel_type="feishu",
            notification_target_id="oc_test_chat",
            prompt_text="Summarize current blockers",
            status="completed",
            result_text="Done",
        )
        session.add(run)
        session.commit()
        session.refresh(run)

        command = parse_command_text(
            "/codex_status run={0}".format(run.id),
            channel="feishu",
            sender_id="ou_test_user",
            chat_id="oc_test_chat",
        )
        result = router.handle(session, command)

        assert result.success is True
        assert result.command_name == "codex_status"
        assert result.status == "completed"
        assert result.payload["result_text"] == "Done"


def test_command_router_treats_plain_text_as_codex_run():
    from app.core.config import Settings
    from app.db.models.codex_run import CodexRun

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    dispatcher = FakeDispatcher()
    router = CommandRouter(
        dispatcher=dispatcher,
        notification_service=FakeNotificationService(),
        settings=Settings(_env_file=None, LLM_API_KEY="test-key"),
    )
    command = parse_command_text(
        "Summarize the current test strategy in one sentence",
        channel="feishu",
        sender_id="ou_test_user",
        chat_id="oc_test_chat",
    )

    with Session(engine) as session:
        result = router.handle(session, command)
        run = session.query(CodexRun).order_by(CodexRun.id.desc()).one()

        assert result.success is True
        assert result.command_name == "run_codex"
        assert run.prompt_text == "Summarize the current test strategy in one sentence"
        assert dispatcher.codex_calls == [run.id]
