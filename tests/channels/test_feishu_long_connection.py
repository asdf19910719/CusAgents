from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.commands.router import CommandRouter
from app.core.config import Settings
from app.db.base import Base


class FakeDispatcher:
    def enqueue_job(self, job_id):
        return {"dispatch_status": "enqueued", "queue_name": "lc-queue"}


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


def _build_event(text, message_type="text", chat_id="oc_test_chat", open_id="ou_test_user"):
    from lark_oapi.api.im.v1.model.p2_im_message_receive_v1 import P2ImMessageReceiveV1

    return P2ImMessageReceiveV1(
        {
            "event": {
                "sender": {
                    "sender_id": {
                        "open_id": open_id,
                    },
                    "sender_type": "user",
                },
                "message": {
                    "chat_id": chat_id,
                    "message_type": message_type,
                    "content": '{"text":"' + text.replace('"', '\\"') + '"}',
                },
            }
        }
    )


def test_long_connection_handler_processes_text_message_and_sends_command_result():
    from app.channels.feishu_long_connection import FeishuLongConnectionHandler

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    notification_service = FakeNotificationService()
    settings = Settings(_env_file=None, LLM_API_KEY="test-key")

    def command_router_factory():
        return CommandRouter(
            dispatcher=FakeDispatcher(),
            notification_service=notification_service,
            settings=settings,
        )

    handler = FeishuLongConnectionHandler(
        session_factory=session_factory,
        command_router_factory=command_router_factory,
    )

    result = handler.handle_message_receive_v1(
        _build_event('/create topic="赛博 武侠" style=cinematic shots=2 backend=third_party')
    )

    assert result.success is True
    assert result.command_name == "create_job"
    assert result.status == "pending"
    assert notification_service.calls[0]["event_type"] == "job_created"
    assert notification_service.calls[-1]["event_type"] == "command_result"
    assert notification_service.calls[-1]["target_id"] == "oc_test_chat"


def test_long_connection_handler_ignores_non_text_messages():
    from app.channels.feishu_long_connection import FeishuLongConnectionHandler

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    handler = FeishuLongConnectionHandler(
        session_factory=session_factory,
        command_router_factory=lambda: CommandRouter(
            dispatcher=FakeDispatcher(),
            notification_service=FakeNotificationService(),
            settings=Settings(_env_file=None, LLM_API_KEY="test-key"),
        ),
    )

    result = handler.handle_message_receive_v1(_build_event("ignored", message_type="image"))

    assert result is None


def test_long_connection_client_builder_uses_sdk_client_and_registers_handler():
    from app.channels.feishu_long_connection import FeishuLongConnectionHandler, FeishuLongConnectionRunner

    captured = {}

    class FakeEventDispatcherBuilder:
        def __init__(self, verification_token, encrypt_key):
            captured["verification_token"] = verification_token
            captured["encrypt_key"] = encrypt_key

        def register_p2_im_message_receive_v1(self, callback):
            captured["callback"] = callback
            return self

        def build(self):
            return "fake-event-handler"

    class FakeEventDispatcherRoot:
        @staticmethod
        def builder(verification_token, encrypt_key):
            return FakeEventDispatcherBuilder(verification_token, encrypt_key)

    class FakeWsClient:
        def __init__(self, app_id, app_secret, event_handler=None, **kwargs):
            captured["app_id"] = app_id
            captured["app_secret"] = app_secret
            captured["event_handler"] = event_handler
            captured["kwargs"] = kwargs

    handler = FeishuLongConnectionHandler(
        session_factory=lambda: None,
        command_router_factory=lambda: None,
    )
    settings = Settings(
        _env_file=None,
        LLM_API_KEY="test-key",
        FEISHU_APP_ID="cli_test",
        FEISHU_APP_SECRET="secret_test",
        FEISHU_VERIFICATION_TOKEN="token_test",
        FEISHU_ENCRYPT_KEY="encrypt_test",
    )

    runner = FeishuLongConnectionRunner(
        settings=settings,
        handler=handler,
        ws_client_cls=FakeWsClient,
        event_dispatcher_cls=FakeEventDispatcherRoot,
    )

    client = runner.build_client()

    assert isinstance(client, FakeWsClient)
    assert captured["app_id"] == "cli_test"
    assert captured["app_secret"] == "secret_test"
    assert captured["event_handler"] == "fake-event-handler"
    assert captured["verification_token"] == "token_test"
    assert captured["encrypt_key"] == "encrypt_test"
    assert captured["callback"] == handler.handle_message_receive_v1


def test_long_connection_runner_can_connect_check_without_blocking():
    from app.channels.feishu_long_connection import FeishuLongConnectionHandler, FeishuLongConnectionRunner

    captured = {"connect_called": 0, "disconnect_called": 0}

    class FakeEventDispatcherBuilder:
        def register_p2_im_message_receive_v1(self, callback):
            return self

        def build(self):
            return "fake-event-handler"

    class FakeEventDispatcherRoot:
        @staticmethod
        def builder(verification_token, encrypt_key):
            return FakeEventDispatcherBuilder()

    class FakeWsClient:
        def __init__(self, app_id, app_secret, event_handler=None, **kwargs):
            self.app_id = app_id
            self.app_secret = app_secret
            self.event_handler = event_handler

        async def _connect(self):
            captured["connect_called"] += 1

        async def _disconnect(self):
            captured["disconnect_called"] += 1

    handler = FeishuLongConnectionHandler(
        session_factory=lambda: None,
        command_router_factory=lambda: None,
    )
    settings = Settings(
        _env_file=None,
        LLM_API_KEY="test-key",
        FEISHU_APP_ID="cli_test",
        FEISHU_APP_SECRET="secret_test",
    )
    runner = FeishuLongConnectionRunner(
        settings=settings,
        handler=handler,
        ws_client_cls=FakeWsClient,
        event_dispatcher_cls=FakeEventDispatcherRoot,
    )

    runner.connect_check()

    assert captured["connect_called"] == 1
    assert captured["disconnect_called"] == 1


def test_long_connection_runner_connect_check_cancels_pending_tasks():
    import asyncio

    from app.channels.feishu_long_connection import FeishuLongConnectionHandler, FeishuLongConnectionRunner

    captured = {"background_task": None}

    class FakeEventDispatcherBuilder:
        def register_p2_im_message_receive_v1(self, callback):
            return self

        def build(self):
            return "fake-event-handler"

    class FakeEventDispatcherRoot:
        @staticmethod
        def builder(verification_token, encrypt_key):
            return FakeEventDispatcherBuilder()

    class FakeWsClient:
        def __init__(self, app_id, app_secret, event_handler=None, **kwargs):
            self.app_id = app_id
            self.app_secret = app_secret
            self.event_handler = event_handler

        async def _connect(self):
            captured["background_task"] = asyncio.get_running_loop().create_task(asyncio.sleep(60))

        async def _disconnect(self):
            return None

    handler = FeishuLongConnectionHandler(
        session_factory=lambda: None,
        command_router_factory=lambda: None,
    )
    settings = Settings(
        _env_file=None,
        LLM_API_KEY="test-key",
        FEISHU_APP_ID="cli_test",
        FEISHU_APP_SECRET="secret_test",
    )
    runner = FeishuLongConnectionRunner(
        settings=settings,
        handler=handler,
        ws_client_cls=FakeWsClient,
        event_dispatcher_cls=FakeEventDispatcherRoot,
    )

    runner.connect_check()

    assert captured["background_task"] is not None
    assert captured["background_task"].cancelled() is True
