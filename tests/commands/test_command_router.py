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

    def enqueue_video_job(self, video_id):
        self.job_calls.append(("video", video_id))
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
        assert run.conversation_session_id is not None
        assert run.resolved_prompt_text
        assert "Summarize current blockers" in run.resolved_prompt_text
        assert dispatcher.codex_calls == [run.id]


def test_command_router_creates_video_job_and_enqueues_it():
    from app.core.config import Settings
    from app.db.models.video_job import VideoJob

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    dispatcher = FakeDispatcher()
    router = CommandRouter(
        dispatcher=dispatcher,
        notification_service=FakeNotificationService(),
        settings=Settings(_env_file=None, LLM_API_KEY="test-key"),
    )
    command = parse_command_text(
        '/video prompt="cinematic city sunrise" duration=4 ratio=16:9 model=seedance2.0',
        channel="feishu",
        sender_id="ou_test_user",
        chat_id="oc_test_chat",
    )

    with Session(engine) as session:
        result = router.handle(session, command)
        video = session.query(VideoJob).order_by(VideoJob.id.desc()).one()

        assert result.success is True
        assert result.command_name == "create_video"
        assert result.payload["dispatch_status"] == "enqueued"
        assert result.payload["video_id"] == video.id
        assert video.prompt == "cinematic city sunrise"
        assert video.notification_target_id == "oc_test_chat"
        assert dispatcher.job_calls == [("video", video.id)]


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
        assert run.conversation_session_id is not None
        assert dispatcher.codex_calls == [run.id]


def test_command_router_resets_conversation_for_new_command():
    from app.core.config import Settings

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    router = CommandRouter(
        dispatcher=FakeDispatcher(),
        notification_service=FakeNotificationService(),
        settings=Settings(_env_file=None, LLM_API_KEY="test-key"),
    )
    command = parse_command_text(
        "/new",
        channel="feishu",
        sender_id="ou_test_user",
        chat_id="oc_test_chat",
    )

    with Session(engine) as session:
        result = router.handle(session, command)

        assert result.success is True
        assert result.command_name == "reset_conversation"


def test_command_router_allows_run_codex_without_chat_id():
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
        '/codex prompt="Summarize current blockers"',
        channel="feishu",
        sender_id="ou_test_user",
        chat_id=None,
    )

    with Session(engine) as session:
        result = router.handle(session, command)
        run = session.query(CodexRun).order_by(CodexRun.id.desc()).one()

        assert result.success is True
        assert run.conversation_session_id is None
        assert run.resolved_prompt_text == run.prompt_text


def test_command_router_uses_locked_conversation_access_for_chat_messages():
    from app.core.config import Settings
    from app.db.models.codex_run import CodexRun

    class TrackingConversationService(object):
        def __init__(self):
            self.acquire_lock_flags = []

        def get_or_create_session(self, session, chat_id, now=None, acquire_lock=False):
            from app.db.models.conversation_session import ConversationSession

            self.acquire_lock_flags.append(acquire_lock)
            conversation = ConversationSession(chat_id=chat_id, status="active")
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            return conversation

        def append_message(self, session, conversation, role, content_text, source_type, source_run_id=None):
            return None

        def compact_if_needed(self, session, conversation):
            return None

        def build_resolved_prompt(self, session, conversation, current_prompt):
            return "resolved:" + current_prompt

    class TrackingRouter(CommandRouter):
        def __init__(self, conversation_service, *args, **kwargs):
            CommandRouter.__init__(self, *args, **kwargs)
            self._tracking_conversation_service = conversation_service

        def _build_conversation_service(self):
            return self._tracking_conversation_service

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    dispatcher = FakeDispatcher()
    tracking_service = TrackingConversationService()
    router = TrackingRouter(
        conversation_service=tracking_service,
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
        assert run.resolved_prompt_text == "resolved:Summarize the current test strategy in one sentence"
        assert tracking_service.acquire_lock_flags == [True]
