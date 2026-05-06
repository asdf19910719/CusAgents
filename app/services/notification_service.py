import httpx

from app.db.models.outbound_notification import OutboundNotification


class FeishuAppMessageNotifier:
    def __init__(self, app_id, app_secret, open_base_url="https://open.feishu.cn/open-apis", http_client=None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.open_base_url = open_base_url.rstrip("/")
        self.http_client = http_client or httpx.Client(timeout=30.0, trust_env=False)

    def send_message(self, message, target_id=None):
        if not target_id:
            raise ValueError("target_id is required for feishu app message sending")
        token = self._get_tenant_access_token()
        response = self.http_client.post(
            self.open_base_url + "/im/v1/messages?receive_id_type=chat_id",
            headers={"Authorization": "Bearer " + token},
            json={
                "receive_id": target_id,
                "msg_type": "text",
                "content": "{\"text\":\"" + message.replace("\\", "\\\\").replace("\"", "\\\"") + "\"}",
            },
        )
        response.raise_for_status()
        return response.json()

    def _get_tenant_access_token(self):
        response = self.http_client.post(
            self.open_base_url + "/auth/v3/tenant_access_token/internal",
            json={
                "app_id": self.app_id,
                "app_secret": self.app_secret,
            },
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("tenant_access_token")
        if not token:
            raise RuntimeError("missing tenant_access_token")
        return token


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
