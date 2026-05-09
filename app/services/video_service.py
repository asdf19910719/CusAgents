from pathlib import Path
import os

from app.db.models.video_asset import VideoAsset
from app.providers.image.dreamina_cli_client import DreaminaCliError
from app.providers.video.base import VideoGenerationRequest
from app.services.video_notification_messages import build_video_completion_message, build_video_failure_message


class VideoService:
    def __init__(self, provider, output_dir, notification_service=None):
        self.provider = provider
        self.output_dir = Path(output_dir)
        self.notification_service = notification_service
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_video_job(self, session, job):
        job.status = "running"
        job.current_step = job.mode or "text2video"
        session.commit()
        try:
            generation_input = self._build_generation_input(job)
            result = self.provider.generate_video(
                generation_input,
                duration=job.duration,
                ratio=job.ratio,
                video_resolution=job.video_resolution,
                model_version=job.model_version,
            )
            file_path = self.output_dir / ("video-{0}-{1}{2}".format(job.id, result.file_name, result.file_extension))
            file_path.write_bytes(result.video_bytes)
            job.status = "completed"
            job.current_step = "completed"
            job.submit_id = result.remote_job_id
            job.error_message = None
            asset = VideoAsset(
                video_job_id=job.id,
                file_path=str(file_path),
                preview_path=str(file_path),
                thumbnail_path=None,
                duration=result.duration,
                ratio=result.ratio,
                video_resolution=result.video_resolution,
                status="completed",
                metadata_json=result.metadata,
            )
            session.add(asset)
            session.commit()
            session.refresh(job)
            self._notify(
                session,
                job,
                "video_job_completed",
                build_video_completion_message(job, asset=asset, file_path=str(file_path)),
            )
            return job
        except DreaminaCliError as exc:
            job.submit_id = exc.submit_id
            job.status = "querying" if exc.gen_status in ("querying", "timeout") else "failed"
            job.current_step = "query_result" if job.status == "querying" else "failed"
            job.error_message = str(exc)
            session.commit()
            session.refresh(job)
            if job.status == "failed":
                self._notify(
                    session,
                    job,
                    "video_job_failed",
                    build_video_failure_message(job, str(exc)),
                )
            return job
        except Exception as exc:
            job.status = "failed"
            job.current_step = "failed"
            job.error_message = str(exc)
            session.commit()
            session.refresh(job)
            self._notify(
                session,
                job,
                "video_job_failed",
                build_video_failure_message(job, str(exc)),
            )
            return job

    def _build_generation_input(self, job):
        manifest = getattr(job, "reference_manifest_json", None) or {}
        image_items = manifest.get("images") if isinstance(manifest, dict) else None
        if not image_items and (job.mode or "text2video") == "text2video":
            return job.prompt
        reference_images = []
        reference_image_usages = []
        for item in image_items or []:
            file_path = item.get("file_path")
            if file_path:
                reference_images.append(self._resolve_reference_image_path(file_path))
                reference_image_usages.append(item)
        return VideoGenerationRequest(
            prompt=job.prompt,
            mode=job.mode or "text2video",
            reference_images=reference_images,
            reference_image_usages=reference_image_usages,
            duration=job.duration,
            ratio=job.ratio,
            video_resolution=job.video_resolution,
            model_version=job.model_version,
            submit_id=job.submit_id,
        )

    def _resolve_reference_image_path(self, file_path):
        text = str(file_path)
        prefix = "/app/projects/"
        host_root = os.environ.get("ARCREEL_PROJECTS_HOST_ROOT")
        if text.startswith(prefix) and host_root:
            candidate = Path(host_root) / text[len(prefix):]
            if candidate.exists():
                return str(candidate)
        return text

    def _notify(self, session, job, event_type, message):
        if self.notification_service is None:
            return
        if hasattr(self.notification_service, "notify_video_job_event"):
            self.notification_service.notify_video_job_event(session, job, event_type=event_type, message=message)
