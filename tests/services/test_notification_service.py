import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.enums import JobStatus
from app.db.base import Base
from app.db.models.job import Job
from app.services.notification_service import (
    FeishuAppMessageNotifier,
    FeishuWebhookNotifier,
    NotificationService,
)


def create_job(session):
    job = Job(
        request_id="req-notify",
        topic="冷血剑客复仇",
        style_preset="cinematic",
        target_shot_count=2,
        image_backend="third_party",
        status=JobStatus.PENDING,
        idempotency_key="notify-key",
        current_step="outline",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def build_transport(status_code=200, payload=None):
    def handler(request):
        assert request.method == "POST"
        return httpx.Response(status_code, json=payload or {"code": 0, "msg": "ok"})

    return httpx.MockTransport(handler)


def test_notification_service_records_sent_notification():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    notifier = FeishuWebhookNotifier(
        webhook_url="https://example.com/webhook",
        http_client=httpx.Client(
            transport=build_transport(),
            base_url="https://example.com",
        ),
    )
    service = NotificationService(notifier=notifier)

    with Session(engine) as session:
        job = create_job(session)

        record = service.notify_job_event(session, job, event_type="job_created", message="任务已创建")

        assert record.status == "sent"
        assert record.channel_type == "feishu"
        assert record.job_id == job.id
        assert record.event_type == "job_created"
        assert record.payload_json["message"] == "任务已创建"


def test_notification_service_records_failed_notification():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    notifier = FeishuWebhookNotifier(
        webhook_url="https://example.com/webhook",
        http_client=httpx.Client(
            transport=build_transport(status_code=500, payload={"code": 500, "msg": "failed"}),
            base_url="https://example.com",
        ),
    )
    service = NotificationService(notifier=notifier)

    with Session(engine) as session:
        job = create_job(session)

        record = service.notify_job_event(session, job, event_type="job_failed", message="任务失败")

        assert record.status == "failed"
        assert "500" in (record.error_message or "")


def test_feishu_app_message_notifier_sends_message_to_chat_id():
    calls = []

    def handler(request):
        calls.append((request.method, request.url.path, request.url.query, request.content.decode("utf-8")))
        if request.url.path.endswith("/tenant_access_token/internal"):
            return httpx.Response(200, json={"tenant_access_token": "tenant-token"})
        return httpx.Response(200, json={"code": 0, "data": {"message_id": "om_123"}})

    notifier = FeishuAppMessageNotifier(
        app_id="cli_a",
        app_secret="secret_b",
        open_base_url="https://open.feishu.cn/open-apis",
        http_client=httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://open.feishu.cn",
        ),
    )

    payload = notifier.send_message("任务已完成", target_id="oc_test_chat")

    assert payload["data"]["message_id"] == "om_123"
    assert calls[0][1].endswith("/auth/v3/tenant_access_token/internal")
    assert "/im/v1/messages" in calls[1][1]
    assert "receive_id_type=chat_id" in calls[1][2].decode("utf-8")


def test_feishu_app_message_notifier_serializes_multiline_text_content():
    calls = []

    def handler(request):
        calls.append((request.url.path, request.content.decode("utf-8")))
        if request.url.path.endswith("/tenant_access_token/internal"):
            return httpx.Response(200, json={"tenant_access_token": "tenant-token"})
        return httpx.Response(200, json={"code": 0, "data": {"message_id": "om_456"}})

    notifier = FeishuAppMessageNotifier(
        app_id="cli_a",
        app_secret="secret_b",
        open_base_url="https://open.feishu.cn/open-apis",
        http_client=httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://open.feishu.cn",
        ),
    )

    notifier.send_message("line1\nline2\nline3", target_id="oc_test_chat")

    assert "\\n" in calls[1][1]


def test_notification_service_skips_app_message_without_target_id():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    notifier = FeishuAppMessageNotifier(
        app_id="cli_a",
        app_secret="secret_b",
        open_base_url="https://open.feishu.cn/open-apis",
        http_client=httpx.Client(
            transport=build_transport(),
            base_url="https://open.feishu.cn",
        ),
    )
    service = NotificationService(notifier=notifier)

    with Session(engine) as session:
        job = create_job(session)

        record = service.notify_job_event(session, job, event_type="job_created", message="created", target_id=None)

        assert record.status == "skipped"


def test_notification_service_uses_job_notification_target_id():
    calls = []

    def handler(request):
        calls.append((request.url.path, request.content.decode("utf-8")))
        if request.url.path.endswith("/tenant_access_token/internal"):
            return httpx.Response(200, json={"tenant_access_token": "tenant-token"})
        return httpx.Response(200, json={"code": 0, "data": {"message_id": "om_789"}})

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    notifier = FeishuAppMessageNotifier(
        app_id="cli_a",
        app_secret="secret_b",
        open_base_url="https://open.feishu.cn/open-apis",
        http_client=httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://open.feishu.cn",
        ),
    )
    service = NotificationService(notifier=notifier)

    with Session(engine) as session:
        job = create_job(session)
        job.notification_target_id = "oc_target_from_job"
        session.commit()
        session.refresh(job)

        record = service.notify_job_event(session, job, event_type="job_waiting_review", message="done", target_id=None)

        assert record.status == "sent"
        assert record.target_id == "oc_target_from_job"
        assert len(calls) == 2
