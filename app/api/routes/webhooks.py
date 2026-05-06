import hashlib
import hmac
import json
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.routes.jobs import get_job_dispatcher, get_notification_service
from app.commands.parser import parse_command_text
from app.commands.router import CommandRouter
from app.core.config import load_settings


router = APIRouter(prefix="/webhooks", tags=["webhooks"])
_SEEN_FEISHU_REQUESTS = {}


def get_command_router(
    dispatcher=Depends(get_job_dispatcher),
    notification_service=Depends(get_notification_service),
):
    settings = load_settings(allow_placeholder_llm_api_key=True)
    return CommandRouter(
        dispatcher=dispatcher,
        notification_service=notification_service,
        settings=settings,
    )


@router.post("/feishu/events")
async def handle_feishu_events(
    request: Request,
    db: Session = Depends(get_db),
    command_router: CommandRouter = Depends(get_command_router),
):
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid request json") from exc

    if payload.get("type") == "url_verification" and "challenge" in payload:
        return {"challenge": payload["challenge"]}

    settings = load_settings(allow_placeholder_llm_api_key=True)
    verification_token = settings.feishu_verification_token
    if verification_token:
        token = payload.get("token")
        if token != verification_token:
            raise HTTPException(status_code=403, detail="invalid feishu verification token")
    _verify_feishu_signature(raw_body, request.headers, settings)

    event = payload.get("event") or {}
    message = event.get("message") or {}
    if message.get("message_type") != "text":
        raise HTTPException(status_code=400, detail="unsupported message type")

    try:
        content_payload = json.loads(message.get("content") or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid message content") from exc

    text = content_payload.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty command text")

    sender = event.get("sender") or {}
    sender_id = (sender.get("sender_id") or {}).get("open_id") or "unknown"
    command = parse_command_text(
        text,
        channel="feishu",
        sender_id=sender_id,
        chat_id=message.get("chat_id"),
    )
    result = command_router.handle(db, command)
    notification_service = command_router.notification_service
    if notification_service is not None:
        notification_service.notify_job_event(
            db,
            None,
            event_type="command_result",
            message=_format_command_result_message(result),
            target_id=message.get("chat_id"),
        )
    return result.model_dump()


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


def _verify_feishu_signature(raw_body, headers, settings):
    encrypt_key = (settings.feishu_encrypt_key or "").strip()
    if not encrypt_key:
        return

    timestamp = headers.get("x-lark-request-timestamp", "").strip()
    nonce = headers.get("x-lark-request-nonce", "").strip()
    signature = headers.get("x-lark-signature", "").strip()
    if not timestamp or not nonce or not signature:
        raise HTTPException(status_code=403, detail="missing feishu signature headers")

    try:
        request_timestamp = int(timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="invalid feishu timestamp") from exc

    now = int(time.time())
    if abs(now - request_timestamp) > settings.feishu_webhook_max_age_seconds:
        raise HTTPException(status_code=403, detail="expired feishu request")

    expected_signature = hashlib.sha256(
        timestamp.encode("utf-8") + nonce.encode("utf-8") + encrypt_key.encode("utf-8") + raw_body
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=403, detail="invalid feishu signature")

    replay_key = "{0}:{1}:{2}".format(timestamp, nonce, signature)
    _cleanup_seen_requests(now, settings.feishu_webhook_max_age_seconds)
    if replay_key in _SEEN_FEISHU_REQUESTS:
        raise HTTPException(status_code=403, detail="replayed feishu request")
    _SEEN_FEISHU_REQUESTS[replay_key] = now


def _cleanup_seen_requests(now, ttl_seconds):
    expired_keys = []
    for replay_key, seen_at in _SEEN_FEISHU_REQUESTS.items():
        if now - seen_at > ttl_seconds:
            expired_keys.append(replay_key)
    for replay_key in expired_keys:
        _SEEN_FEISHU_REQUESTS.pop(replay_key, None)
