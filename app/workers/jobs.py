from app.db.models.job import Job
from app.db.models.codex_run import CodexRun
from app.db.session import SessionLocal
from app.core.config import load_settings
from app.services.factory import build_codex_run_service, build_notification_service, build_orchestration_service
from app.services.codex_run_service import CodexRunService


def execute_job(job_id, session_factory, orchestration_service, model_name):
    session = session_factory()
    try:
        job = session.get(Job, job_id)
        updated_job = orchestration_service.run_job(session, job, model_name=model_name)
        return {"job_id": updated_job.id, "status": updated_job.status}
    finally:
        session.close()


def run_default_job(job_id, orchestration_service, model_name):
    return execute_job(
        job_id=job_id,
        session_factory=SessionLocal,
        orchestration_service=orchestration_service,
        model_name=model_name,
    )


def run_configured_job(job_id):
    settings = load_settings()
    orchestration_service = build_orchestration_service(settings)
    return execute_job(
        job_id=job_id,
        session_factory=SessionLocal,
        orchestration_service=orchestration_service,
        model_name=settings.llm_default_model,
    )


def execute_codex_run(run_id, session_factory, codex_run_service: CodexRunService, notification_service):
    session = session_factory()
    try:
        run = session.get(CodexRun, run_id)
        run.status = "running"
        session.commit()
        result = codex_run_service.execute_run(run_id=run.id, prompt_text=run.prompt_text)
        run.status = result["status"]
        run.result_text = result["result_text"]
        run.output_text_path = result["output_text_path"]
        run.image_paths_json = codex_run_service.encode_image_paths(result["image_paths"])
        run.error_message = None
        session.commit()
        session.refresh(run)
        if notification_service is not None:
            summary = [
                "codex 任务已完成",
                "run_id={0}".format(run.id),
                "status={0}".format(run.status),
            ]
            if run.result_text:
                summary.append("result={0}".format(run.result_text[:500]))
            notification_service.notify_job_event(
                session,
                run,
                event_type="codex_run_completed",
                message="\n".join(summary),
                target_id=run.notification_target_id,
            )
            for image_path in result["image_paths"]:
                class CodexAssetPreview:
                    id = None

                    def __init__(self, path):
                        self.file_path = path
                        self.preview_path = path

                notification_service.notify_asset_image(
                    session,
                    run,
                    CodexAssetPreview(image_path),
                    event_type="codex_run_image",
                    target_id=run.notification_target_id,
                )
        return {"run_id": run.id, "status": run.status}
    except Exception as exc:
        run = session.get(CodexRun, run_id)
        if run is not None:
            run.status = "failed"
            run.error_message = str(exc)
            session.commit()
            session.refresh(run)
            if notification_service is not None:
                notification_service.notify_job_event(
                    session,
                    run,
                    event_type="codex_run_failed",
                    message="codex 任务执行失败: {0}".format(str(exc)),
                    target_id=run.notification_target_id,
                )
        raise
    finally:
        session.close()


def run_configured_codex_run(run_id):
    settings = load_settings()
    codex_run_service = build_codex_run_service(settings)
    notification_service = build_notification_service(settings)
    return execute_codex_run(
        run_id=run_id,
        session_factory=SessionLocal,
        codex_run_service=codex_run_service,
        notification_service=notification_service,
    )
