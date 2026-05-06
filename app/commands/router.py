import uuid

from app.commands.schemas import CommandResult
from app.core.config import load_settings
from app.db.models.asset import Asset
from app.db.models.command_log import CommandLog
from app.db.models.job import Job
from app.db.models.review import Review
from app.db.models.step_run import StepRun
from app.services.runtime_health_service import RuntimeHealthService


class CommandRouter:
    def __init__(self, dispatcher, notification_service=None, settings=None):
        self.dispatcher = dispatcher
        self.notification_service = notification_service
        self.settings = settings or load_settings(allow_placeholder_llm_api_key=True)

    def handle(self, session, command):
        try:
            result = self._dispatch(session, command)
            self._record_command(session, command, result)
            return result
        except Exception as exc:
            self._record_command(
                session,
                command,
                CommandResult(
                    success=False,
                    command_name=command.command_name,
                    message=str(exc),
                ),
                error_message=str(exc),
            )
            raise

    def _dispatch(self, session, command):
        name = command.command_name
        if name == "create_job":
            return self._create_job(session, command)
        if name == "job_status":
            return self._job_status(session, command)
        if name == "retry_job":
            return self._retry_job(session, command)
        if name == "approve_job":
            return self._approve_job(session, command)
        if name == "cancel_job":
            return self._cancel_job(session, command)
        if name == "list_assets":
            return self._list_assets(session, command)
        if name == "runtime_health":
            return self._runtime_health(session, command)
        raise ValueError("unsupported command: " + name)

    def _create_job(self, session, command):
        arguments = command.arguments
        job = Job(
            request_id=str(uuid.uuid4()),
            topic=arguments["topic"],
            style_preset=arguments["style_preset"],
            target_shot_count=arguments["target_shot_count"],
            image_backend=arguments["image_backend"],
            status="pending",
            idempotency_key=str(uuid.uuid4()),
            current_step="outline",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        if self.notification_service is not None:
            self.notification_service.notify_job_event(
                session,
                job,
                event_type="job_created",
                message="任务已创建，job_id={0}".format(job.id),
                target_id=command.chat_id,
            )
        dispatch_result = self._safe_enqueue(job.id)
        return CommandResult(
            success=True,
            command_name=command.command_name,
            message="任务已创建",
            job_id=job.id,
            status=job.status,
            payload=dispatch_result,
        )

    def _job_status(self, session, command):
        job = self._require_job(session, command.arguments["job_id"])
        return CommandResult(
            success=True,
            command_name=command.command_name,
            message="任务状态已返回",
            job_id=job.id,
            status=job.status,
            payload={
                "current_step": job.current_step,
                "style_preset": job.style_preset,
                "target_shot_count": job.target_shot_count,
                "image_backend": job.image_backend,
                "error_message": job.error_message,
            },
        )

    def _retry_job(self, session, command):
        job = self._require_job(session, command.arguments["job_id"])
        job.status = "pending"
        session.commit()
        dispatch_result = self._safe_enqueue(job.id)
        return CommandResult(
            success=True,
            command_name=command.command_name,
            message="任务已重试",
            job_id=job.id,
            status=job.status,
            payload=dispatch_result,
        )

    def _approve_job(self, session, command):
        job = self._require_job(session, command.arguments["job_id"])
        job.status = "completed"
        review = Review(
            job_id=job.id,
            review_type="manual",
            result="approved",
            score=1,
            notes="approved via command",
            reviewed_by=command.sender_id,
        )
        session.add(review)
        session.commit()
        return CommandResult(
            success=True,
            command_name=command.command_name,
            message="任务已审核通过",
            job_id=job.id,
            status=job.status,
        )

    def _cancel_job(self, session, command):
        job = self._require_job(session, command.arguments["job_id"])
        job.status = "cancelled"
        session.commit()
        return CommandResult(
            success=True,
            command_name=command.command_name,
            message="任务已取消",
            job_id=job.id,
            status=job.status,
        )

    def _list_assets(self, session, command):
        job = self._require_job(session, command.arguments["job_id"])
        assets = session.query(Asset).filter_by(job_id=job.id).order_by(Asset.id).all()
        return CommandResult(
            success=True,
            command_name=command.command_name,
            message="任务素材已返回",
            job_id=job.id,
            status=job.status,
            payload={
                "assets": [
                    {
                        "id": asset.id,
                        "shot_index": asset.shot_index,
                        "status": asset.status,
                        "file_path": asset.file_path,
                    }
                    for asset in assets
                ]
            },
        )

    def _runtime_health(self, session, command):
        result = RuntimeHealthService(self.settings).collect(session)
        return CommandResult(
            success=True,
            command_name=command.command_name,
            message="运行状态已返回",
            status=result["status"],
            payload=result,
        )

    def _require_job(self, session, job_id):
        job = session.get(Job, job_id)
        if job is None:
            raise ValueError("job not found")
        return job

    def _safe_enqueue(self, job_id):
        try:
            result = self.dispatcher.enqueue_job(job_id)
            return {
                "dispatch_status": result["dispatch_status"],
                "queue_name": result["queue_name"],
                "dispatch_error": None,
            }
        except Exception as exc:
            return {
                "dispatch_status": "failed",
                "queue_name": None,
                "dispatch_error": str(exc),
            }

    def _record_command(self, session, command, result, error_message=None):
        related_job_id = result.job_id if result.job_id is not None else None
        log = CommandLog(
            request_id=command.request_id,
            channel_type=command.channel,
            sender_id=command.sender_id,
            command_name=command.command_name,
            raw_text=command.raw_text,
            arguments_json=command.arguments,
            result_status="success" if result.success else "failed",
            related_job_id=related_job_id,
            error_message=error_message,
        )
        session.add(log)
        session.commit()
