import socket
from urllib.parse import urlparse

from redis import Redis
from sqlalchemy import text


class RuntimeHealthService:
    def __init__(self, settings, redis_ping=None, tcp_check=None):
        self.settings = settings
        self.redis_ping = redis_ping or self._redis_ping
        self.tcp_check = tcp_check or self._tcp_check

    def collect(self, db):
        checks = {
            "database": self._check_database(db),
            "redis": self._check_redis(),
            "llm": self._check_llm(),
            "image_backends": self._check_image_backends(),
        }
        overall_status = "ok"
        for item in checks["image_backends"]["items"].values():
            if item["status"] == "error":
                overall_status = "degraded"
                break
        for key in ("database", "redis", "llm"):
            if checks[key]["status"] == "error":
                overall_status = "degraded"
                break
        if checks["llm"]["status"] == "missing_config":
            overall_status = "degraded"
        return {"status": overall_status, "checks": checks}

    def _check_database(self, db):
        try:
            db.execute(text("SELECT 1"))
            return {"status": "ok"}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    def _check_redis(self):
        result = self.redis_ping(self.settings.redis_url)
        result["enabled"] = self.settings.auto_enqueue_jobs
        return result

    def _check_llm(self):
        if not self.settings.llm_api_key or self.settings.llm_api_key == "placeholder-llm-api-key":
            return {
                "status": "missing_config",
                "base_url": self.settings.llm_base_url,
                "model": self.settings.llm_default_model,
            }
        return {
            "status": "configured",
            "base_url": self.settings.llm_base_url,
            "model": self.settings.llm_default_model,
        }

    def _check_image_backends(self):
        items = {
            "comfyui_remote": self.tcp_check(self.settings.comfyui_base_url),
        }
        items["comfyui_remote"]["base_url"] = self.settings.comfyui_base_url
        if self.settings.third_party_image_base_url:
            items["third_party"] = self.tcp_check(self.settings.third_party_image_base_url)
            items["third_party"]["base_url"] = self.settings.third_party_image_base_url
            items["third_party"]["model"] = self.settings.third_party_image_model
        else:
            items["third_party"] = {"status": "disabled"}
        return {
            "default_backend": self.settings.image_backend,
            "items": items,
        }

    def _redis_ping(self, redis_url):
        try:
            client = Redis.from_url(redis_url, decode_responses=True)
            client.ping()
            return {"status": "ok", "detail": redis_url}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    def _tcp_check(self, url):
        try:
            parsed = urlparse(url)
            port = parsed.port
            if port is None:
                if parsed.scheme == "https":
                    port = 443
                else:
                    port = 80
            with socket.create_connection((parsed.hostname, port), timeout=2):
                return {"status": "ok", "detail": url}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}
