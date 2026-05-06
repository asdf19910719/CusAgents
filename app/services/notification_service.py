import httpx

from app.db.models.outbound_notification import OutboundNotification


class FeishuWebhookNotifier:
    def __init__(self, webhook_url, http_client=None):
        self.webhook_url = webhook_url
        self.http_client = http_client or httpx.Client(timeout=30.0, trust_env=False)

    def send_message(self, message, target_id=None):
        payload = {
            "msg_type": "text",
            "content": {
                "text": message,
            },
        }
        response = self.http_client.post(self.webhook_url, json=payload)
        response.raise_for_status()
        return response.json()


class NotificationService:
    def __init__(self, notifier=None, default_channel_type="feishu"):
        self.notifier = notifier
        self.default_channel_type = default_channel_type

    def notify_job_event(self, session, job, event_type, message, target_id=None):
        record = OutboundNotification(
            job_id=getattr(job, "id", None),
            channel_type=self.default_channel_type,
            target_id=target_id,
            event_type=event_type,
            payload_json={"message": message},
            status="pending",
            retry_count=0,
        )
        session.add(record)
        session.commit()
        session.refresh(record)

        if self.notifier is None:
            record.status = "skipped"
            session.commit()
            session.refresh(record)
            return record

        try:
            response_payload = self.notifier.send_message(message, target_id=target_id)
            record.status = "sent"
            record.payload_json = {
                "message": message,
                "response_payload": response_payload,
            }
            record.error_message = None
        except Exception as exc:
            record.status = "failed"
            record.error_message = str(exc)
        session.commit()
        session.refresh(record)
        return record
