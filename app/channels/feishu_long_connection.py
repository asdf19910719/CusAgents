import json

from lark_oapi import EventDispatcherHandler, LogLevel
from lark_oapi.ws import Client as LarkWsClient

from app.commands.parser import parse_command_text
from app.commands.router import CommandRouter
from app.core.logging import get_logger
from app.services.factory import build_notification_service
from app.workers.dispatcher import build_job_dispatcher


logger = get_logger(__name__)


class FeishuLongConnectionHandler:
    def __init__(self, session_factory, command_router_factory):
        self.session_factory = session_factory
        self.command_router_factory = command_router_factory

    def handle_message_receive_v1(self, data):
        event = getattr(data, "event", None)
        if event is None or getattr(event, "message", None) is None:
            logger.warning("skip empty feishu long connection event")
            return None

        message = event.message
        if getattr(message, "message_type", None) != "text":
            logger.info("skip non-text feishu message event")
            return None

        try:
            content_payload = json.loads(getattr(message, "content", "") or "{}")
        except json.JSONDecodeError:
            logger.warning("skip invalid feishu message content")
            return None

        text = (content_payload.get("text") or "").strip()
        if not text:
            logger.info("skip empty feishu command text")
            return None

        sender = getattr(event, "sender", None)
        sender_id = "unknown"
        if sender is not None and getattr(sender, "sender_id", None) is not None:
            sender_id = getattr(sender.sender_id, "open_id", None) or getattr(sender.sender_id, "user_id", None) or "unknown"

        command = parse_command_text(
            text,
            channel="feishu_long_connection",
            sender_id=sender_id,
            chat_id=getattr(message, "chat_id", None),
        )

        with self.session_factory() as session:
            command_router = self.command_router_factory()
            result = command_router.handle(session, command)
            notification_service = getattr(command_router, "notification_service", None)
            if notification_service is not None:
                notification_service.notify_job_event(
                    session,
                    None,
                    event_type="command_result",
                    message=_format_command_result_message(result),
                    target_id=getattr(message, "chat_id", None),
                )
            return result


class FeishuLongConnectionRunner:
    def __init__(
        self,
        settings,
        handler,
        ws_client_cls=LarkWsClient,
        event_dispatcher_cls=EventDispatcherHandler,
    ):
        self.settings = settings
        self.handler = handler
        self.ws_client_cls = ws_client_cls
        self.event_dispatcher_cls = event_dispatcher_cls

    def build_client(self):
        event_handler = (
            self.event_dispatcher_cls.builder(
                self.settings.feishu_verification_token,
                self.settings.feishu_encrypt_key,
            )
            .register_p2_im_message_receive_v1(self.handler.handle_message_receive_v1)
            .build()
        )
        return self.ws_client_cls(
            self.settings.feishu_app_id,
            self.settings.feishu_app_secret,
            log_level=LogLevel.INFO,
            event_handler=event_handler,
        )

    def start(self):
        logger.info("starting feishu long connection client")
        client = self.build_client()
        client.start()


def build_feishu_long_connection_handler(settings, session_factory):
    def command_router_factory():
        notification_service = build_notification_service(settings)
        return CommandRouter(
            dispatcher=build_job_dispatcher(),
            notification_service=notification_service,
            settings=settings,
        )

    return FeishuLongConnectionHandler(
        session_factory=session_factory,
        command_router_factory=command_router_factory,
    )


def _format_command_result_message(result):
    lines = [
        "命令执行结果",
        "command={0}".format(result.command_name),
        "success={0}".format(str(result.success).lower()),
        "message={0}".format(result.message),
    ]
    if result.job_id is not None:
        lines.append("job_id={0}".format(result.job_id))
    if result.status:
        lines.append("status={0}".format(result.status))
    return "\n".join(lines)
