import uuid

from app.commands.schemas import CommandResult
from app.core.config import load_settings
from app.db.models.asset import Asset
from app.db.models.command_log import CommandLog
from app.db.models.codex_run import CodexRun
from app.db.models.job import Job
from app.db.models.review import Review
from app.db.models.step_run import StepRun
from app.db.models.video_job import VideoJob
from app.services.conversation_service import ConversationService
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
        if name == "run_codex":
            return self._run_codex(session, command)
        if name == "codex_status":
            return self._codex_status(session, command)
        if name == "reset_conversation":
            return self._reset_conversation(session, command)
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
        if name == "create_video":
            return self._create_video(session, command)
        if name == "video_status":
            return self._video_status(session, command)
        raise ValueError("unsupported command: " + name)

    def _create_job(self, session, command):
        arguments = command.arguments
        job = Job(
            request_id=str(uuid.uuid4()),
            topic=arguments["topic"],
            style_preset=arguments["style_preset"],
            target_shot_count=arguments["target_shot_count"],
            image_backend=arguments["image_backend"],
            notification_target_id=command.chat_id,
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

    def _run_codex(self, session, command):
        conversation = None
        resolved_prompt_text = command.arguments["prompt"]
        if command.chat_id:
            conversation_service = self._build_conversation_service()
            conversation = conversation_service.get_or_create_session(session, command.chat_id, acquire_lock=True)
            conversation_service.append_message(
                session,
                conversation,
                role="user",
                content_text=command.arguments["prompt"],
                source_type="codex_command" if command.raw_text.startswith("/codex") else "plain_text",
            )
            conversation_service.compact_if_needed(session, conversation)
            resolved_prompt_text = conversation_service.build_resolved_prompt(
                session,
                conversation,
                current_prompt=command.arguments["prompt"],
            )
        run = CodexRun(
            request_id=str(uuid.uuid4()),
            channel_type=command.channel,
            sender_id=command.sender_id,
            notification_target_id=command.chat_id,
            conversation_session_id=conversation.id if conversation is not None else None,
            prompt_text=command.arguments["prompt"],
            resolved_prompt_text=resolved_prompt_text,
            status="pending",
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        dispatch_result = self._safe_enqueue_codex_run(run.id)
        return CommandResult(
            success=True,
            command_name=command.command_name,
            message="codex 任务已创建",
            run_id=run.id,
            status=run.status,
            payload={
                "run_id": run.id,
                "dispatch_status": dispatch_result["dispatch_status"],
                "queue_name": dispatch_result["queue_name"],
                "dispatch_error": dispatch_result["dispatch_error"],
            },
        )

    def _codex_status(self, session, command):
        run = self._require_codex_run(session, command.arguments["run_id"])
        return CommandResult(
            success=True,
            command_name=command.command_name,
            message="codex 任务状态已返回",
            run_id=run.id,
            status=run.status,
            payload={
                "result_text": run.result_text,
                "output_text_path": run.output_text_path,
                "image_paths_json": run.image_paths_json,
                "error_message": run.error_message,
            },
        )

    def _reset_conversation(self, session, command):
        if not command.chat_id:
            raise ValueError("chat_id required for conversation reset")
        self._build_conversation_service().reset_session(session, command.chat_id, acquire_lock=True)
        return CommandResult(
            success=True,
            command_name=command.command_name,
            message="会话已重置",
            status="reset",
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

    def _create_video(self, session, command):
        arguments = command.arguments
        if arguments["backend"] != "dreamina_video_cli":
            raise ValueError("unsupported video backend: " + arguments["backend"])
        job = VideoJob(
            request_id=str(uuid.uuid4()),
            topic=arguments.get("prompt"),
            prompt=arguments["prompt"],
            backend=arguments["backend"],
            mode="text2video",
            notification_target_id=command.chat_id,
            status="pending",
            current_step="submit",
            duration=arguments["duration"],
            ratio=arguments["ratio"],
            video_resolution=arguments["video_resolution"],
            model_version=arguments["model_version"],
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        dispatch_result = self._safe_enqueue_video(job.id)
        return CommandResult(
            success=True,
            command_name=command.command_name,
            message="视频任务已创建",
            status=job.status,
            payload={
                "video_id": job.id,
                "dispatch_status": dispatch_result["dispatch_status"],
                "queue_name": dispatch_result["queue_name"],
                "dispatch_error": dispatch_result["dispatch_error"],
            },
        )

    def _video_status(self, session, command):
        job = session.get(VideoJob, command.arguments["video_id"])
        if job is None:
            raise ValueError("video job not found")
        return CommandResult(
            success=True,
            command_name=command.command_name,
            message="视频任务状态已返回",
            status=job.status,
            payload={
                "video_id": job.id,
                "current_step": job.current_step,
                "submit_id": job.submit_id,
                "error_message": job.error_message,
            },
        )

    def _require_job(self, session, job_id):
        job = session.get(Job, job_id)
        if job is None:
            raise ValueError("job not found")
        return job

    def _require_codex_run(self, session, run_id):
        run = session.get(CodexRun, run_id)
        if run is None:
            raise ValueError("codex run not found")
        return run

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

    def _safe_enqueue_codex_run(self, run_id):
        try:
            result = self.dispatcher.enqueue_codex_run(run_id)
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

    def _safe_enqueue_video(self, video_id):
        try:
            result = self.dispatcher.enqueue_video_job(video_id)
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

    def _build_conversation_service(self):
        return ConversationService(
            idle_timeout_seconds=self.settings.conversation_idle_timeout_seconds,
            compact_trigger_count=self.settings.conversation_compact_trigger_count,
            keep_recent_count=self.settings.conversation_keep_recent_count,
        )
