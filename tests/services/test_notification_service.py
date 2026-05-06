import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.enums import JobStatus
from app.db.base import Base
from app.db.models.job import Job
from app.services.notification_service import FeishuWebhookNotifier, NotificationService


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
