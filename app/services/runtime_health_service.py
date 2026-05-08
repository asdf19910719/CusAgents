import socket
import subprocess
from pathlib import Path
from shutil import which
from urllib.parse import urlparse

from redis import Redis
from sqlalchemy import text


class RuntimeHealthService:
    def __init__(self, settings, redis_ping=None, tcp_check=None, dreamina_credit_check=None):
        self.settings = settings
        self.redis_ping = redis_ping or self._redis_ping
        self.tcp_check = tcp_check or self._tcp_check
        self.dreamina_credit_check = dreamina_credit_check or self._dreamina_credit_check

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
        items["chatgpt_web"] = self.tcp_check(self.settings.chatgpt_web_base_url)
        items["chatgpt_web"]["base_url"] = self.settings.chatgpt_web_base_url
        items["chatgpt_web"]["profile_dir"] = self.settings.chatgpt_web_profile_dir
        items["chatgpt_web"]["headless"] = self.settings.chatgpt_web_headless
        codex_command = self.settings.codex_cli_command
        codex_path = which(codex_command)
        if codex_path:
            items["codex_cli"] = {"status": "configured", "command": codex_command, "path": codex_path}
        else:
            items["codex_cli"] = {"status": "disabled", "command": codex_command}
        items["dreamina_cli"] = self._check_dreamina_cli()
        return {
            "default_backend": self.settings.image_backend,
            "items": items,
        }

    def _check_dreamina_cli(self):
        command = self.settings.dreamina_cli_path
        resolved_path = which(command) or command
        if not Path(resolved_path).exists():
            return {
                "status": "disabled",
                "command": command,
                "path": resolved_path,
                "credit_status": "unknown",
            }
        item = {
            "status": "configured",
            "command": command,
            "path": resolved_path,
            "model_version": self.settings.dreamina_image_model_version,
            "ratio": self.settings.dreamina_image_ratio,
            "resolution_type": self.settings.dreamina_image_resolution_type,
            "video_model_version": self.settings.dreamina_video_model_version,
            "video_resolution": self.settings.dreamina_video_resolution,
            "credit_status": "unknown",
        }
        try:
            credit_result = self.dreamina_credit_check(resolved_path)
            item["credit_status"] = credit_result["status"]
            item["credit_detail"] = credit_result.get("detail", "")
        except Exception as exc:
            item["credit_status"] = "error"
            item["credit_detail"] = str(exc)
        return item

    def _dreamina_credit_check(self, resolved_path):
        result = subprocess.run(
            [resolved_path, "user_credit"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=15,
        )
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "detail": (result.stdout or result.stderr or "").strip()[:500],
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
