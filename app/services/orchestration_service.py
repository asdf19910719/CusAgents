from app.core.enums import JobStatus


class OrchestrationService:
    def __init__(
        self,
        outline_service,
        storyboard_service,
        prompt_service,
        image_service,
        quality_service,
        notification_service=None,
    ):
        self.outline_service = outline_service
        self.storyboard_service = storyboard_service
        self.prompt_service = prompt_service
        self.image_service = image_service
        self.quality_service = quality_service
        self.notification_service = notification_service

    def run_job(self, session, job, model_name):
        job.status = JobStatus.RUNNING
        job.current_step = "outline"
        session.commit()
        try:
            outline = self.outline_service.generate_outline(session, job, model_name=model_name)
            job.current_step = "storyboard"
            session.commit()
            storyboard = self.storyboard_service.generate_storyboard(
                session, job, outline_text=outline, model_name=model_name
            )
            job.current_step = "prompt"
            session.commit()
            prompts = self.prompt_service.build_prompts(storyboard, style_preset=job.style_preset, version="v1")
            job.current_step = "image"
            session.commit()
            assets = self.image_service.generate_assets(session, job, prompts, job.style_preset)
            job.current_step = "quality"
            session.commit()
            quality_result = self.quality_service.validate_generation(storyboard, prompts, assets)
            if quality_result.result == "passed":
                job.status = JobStatus.WAITING_REVIEW
                job.current_step = "review"
                self._notify(session, job, "job_waiting_review", "任务已生成完成，等待审核")
            else:
                job.status = JobStatus.FAILED
                job.error_message = quality_result.notes
                self._notify(session, job, "job_failed", "任务质量检查未通过: " + quality_result.notes)
            session.commit()
            session.refresh(job)
            return job
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            session.commit()
            self._notify(session, job, "job_failed", "任务执行失败: " + str(exc))
            raise

    def _notify(self, session, job, event_type, message):
        if self.notification_service is not None:
            self.notification_service.notify_job_event(session, job, event_type=event_type, message=message)
