import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.routes.jobs import get_job_dispatcher, get_notification_service
from app.commands.parser import parse_command_text
from app.commands.router import CommandRouter
from app.core.config import load_settings


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


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
def handle_feishu_events(
    payload: dict,
    db: Session = Depends(get_db),
    command_router: CommandRouter = Depends(get_command_router),
):
    if payload.get("type") == "url_verification" and "challenge" in payload:
        return {"challenge": payload["challenge"]}

    settings = load_settings(allow_placeholder_llm_api_key=True)
    verification_token = settings.feishu_verification_token
    if verification_token:
        token = payload.get("token")
        if token != verification_token:
            raise HTTPException(status_code=403, detail="invalid feishu verification token")

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
    return result.model_dump()
