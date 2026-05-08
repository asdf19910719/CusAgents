import json
import mimetypes
from pathlib import Path

import httpx

from app.db.models.outbound_notification import OutboundNotification


class FeishuAppMessageNotifier:
    def __init__(self, app_id, app_secret, open_base_url="https://open.feishu.cn/open-apis", http_client=None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.open_base_url = open_base_url.rstrip("/")
        self.http_client = http_client or httpx.Client(timeout=30.0, trust_env=False)
        self._tenant_access_token = None

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
                "content": json.dumps({"text": message}, ensure_ascii=False),
            },
        )
        if response.is_error:
            raise httpx.HTTPStatusError(
                "Feishu app message send failed: {0}".format(response.text),
                request=response.request,
                response=response,
            )
        return response.json()

    def send_image_file(self, image_path, target_id=None):
        image_key = self._upload_image(image_path)
        return self.send_image(image_key=image_key, target_id=target_id)

    def send_image(self, image_key, target_id=None):
        if not target_id:
            raise ValueError("target_id is required for feishu app image sending")
        token = self._get_tenant_access_token()
        response = self.http_client.post(
            self.open_base_url + "/im/v1/messages?receive_id_type=chat_id",
            headers={"Authorization": "Bearer " + token},
            json={
                "receive_id": target_id,
                "msg_type": "image",
                "content": json.dumps({"image_key": image_key}, ensure_ascii=False),
            },
        )
        if response.is_error:
            raise httpx.HTTPStatusError(
                "Feishu app image send failed: {0}".format(response.text),
                request=response.request,
                response=response,
            )
        return response.json()

    def _get_tenant_access_token(self):
        if self._tenant_access_token:
            return self._tenant_access_token
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
        self._tenant_access_token = token
        return token

    def _upload_image(self, image_path):
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(str(path))
        token = self._get_tenant_access_token()
        mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        with path.open("rb") as image_file:
            response = self.http_client.post(
                self.open_base_url + "/im/v1/images",
                headers={"Authorization": "Bearer " + token},
                data={"image_type": "message"},
                files={"image": (path.name, image_file, mime_type)},
            )
        if response.is_error:
            raise httpx.HTTPStatusError(
                "Feishu image upload failed: {0}".format(response.text),
                request=response.request,
                response=response,
            )
        payload = response.json()
        image_key = (payload.get("data") or {}).get("image_key")
        if not image_key:
            raise RuntimeError("missing image_key")
        return image_key


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
        resolved_target_id = target_id or getattr(job, "notification_target_id", None)
        record = OutboundNotification(
            job_id=self._resolve_job_id(job),
            channel_type=self.default_channel_type,
            target_id=resolved_target_id,
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

        if resolved_target_id is None and isinstance(self.notifier, FeishuAppMessageNotifier):
            record.status = "skipped"
            record.error_message = None
            session.commit()
            session.refresh(record)
            return record

        try:
            response_payload = self.notifier.send_message(message, target_id=resolved_target_id)
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

    def notify_video_job_event(self, session, video_job, event_type, message, target_id=None):
        resolved_target_id = target_id or getattr(video_job, "notification_target_id", None)
        record = OutboundNotification(
            video_job_id=getattr(video_job, "id", None),
            channel_type=self.default_channel_type,
            target_id=resolved_target_id,
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

        if resolved_target_id is None and isinstance(self.notifier, FeishuAppMessageNotifier):
            record.status = "skipped"
            record.error_message = None
            session.commit()
            session.refresh(record)
            return record

        try:
            response_payload = self.notifier.send_message(message, target_id=resolved_target_id)
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

    def notify_asset_image(self, session, job, asset, event_type="job_asset_image", target_id=None):
        resolved_target_id = target_id or getattr(job, "notification_target_id", None)
        image_path = getattr(asset, "preview_path", None) or getattr(asset, "file_path", None)
        record = OutboundNotification(
            job_id=self._resolve_job_id(job),
            channel_type=self.default_channel_type,
            target_id=resolved_target_id,
            event_type=event_type,
            payload_json={"image_path": image_path, "asset_id": getattr(asset, "id", None)},
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

        if resolved_target_id is None or not hasattr(self.notifier, "send_image_file"):
            record.status = "skipped"
            record.error_message = None
            session.commit()
            session.refresh(record)
            return record

        try:
            response_payload = self.notifier.send_image_file(image_path, target_id=resolved_target_id)
            record.status = "sent"
            record.payload_json = {
                "image_path": image_path,
                "asset_id": getattr(asset, "id", None),
                "response_payload": response_payload,
            }
            record.error_message = None
        except Exception as exc:
            record.status = "failed"
            record.error_message = str(exc)
        session.commit()
        session.refresh(record)
        return record

    def _resolve_job_id(self, job):
        if job is None:
            return None
        if getattr(job, "__tablename__", "") == "jobs":
            return getattr(job, "id", None)
        return None
