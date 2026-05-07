from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.asset import Asset
from app.db.models.command_log import CommandLog
from app.db.models.job import Job
from app.db.models.llm_cache import LlmCache
from app.db.models.outbound_notification import OutboundNotification
from app.db.models.prompt_template import PromptTemplate
from app.db.models.review import Review
from app.db.models.step_run import StepRun


def test_core_models_can_be_created_and_related():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        job = Job(
            request_id="req-1",
            topic="冷血剑客复仇",
            style_preset="cinematic",
            target_shot_count=8,
            image_backend="comfyui_remote",
            notification_target_id="chat-123",
            status="pending",
            idempotency_key="idem-1",
            current_step="outline",
        )
        session.add(job)
        session.flush()

        step_run = StepRun(
            job_id=job.id,
            step_name="outline",
            attempt_no=1,
            status="completed",
            provider_name="openai-compatible",
            model_name="gpt-4.1-mini",
            cache_hit=False,
            input_summary="topic: 冷血剑客复仇",
            output_summary="一个剑客踏上复仇之路",
            input_tokens=120,
            output_tokens=260,
            cost=Decimal("0.0130"),
            latency_ms=820,
        )
        cache = LlmCache(
            cache_key="outline:abc",
            step_name="outline",
            model_name="gpt-4.1-mini",
            prompt_version="v1",
            schema_version="v1",
            normalized_input_hash="abc",
            response_payload={"summary": "cached"},
        )
        template = PromptTemplate(
            template_name="outline",
            template_version="v1",
            step_name="outline",
            content="Generate outline for {{ topic }}",
            is_active=True,
        )
        asset = Asset(
            job_id=job.id,
            shot_index=1,
            prompt_text="hero in rain",
            negative_prompt="blurry",
            seed=42,
            workflow_json={"nodes": []},
            file_path="output/shot-1.png",
            preview_path="output/shot-1-preview.png",
            status="completed",
        )
        review = Review(
            job_id=job.id,
            review_type="manual",
            result="approved",
            score=Decimal("0.95"),
            notes="looks good",
            reviewed_by="tester",
        )
        notification = OutboundNotification(
            job_id=job.id,
            channel_type="feishu",
            target_id="chat-123",
            event_type="job_created",
            payload_json={"message": "任务已创建"},
            status="sent",
            retry_count=0,
        )
        command_log = CommandLog(
            request_id="cmd-1",
            channel_type="feishu",
            sender_id="user-123",
            command_name="create_job",
            raw_text="/create topic=冷血剑客复仇 style=cinematic shots=8",
            arguments_json={"topic": "冷血剑客复仇"},
            result_status="success",
            related_job_id=job.id,
        )

        session.add_all([step_run, cache, template, asset, review, notification, command_log])
        session.commit()
        session.refresh(job)

        assert job.id is not None
        assert job.image_backend == "comfyui_remote"
        assert job.notification_target_id == "chat-123"
        assert len(job.step_runs) == 1
        assert job.step_runs[0].cost == Decimal("0.0130")
        assert len(job.assets) == 1
        assert job.assets[0].file_path == "output/shot-1.png"
        assert len(job.reviews) == 1
        assert job.reviews[0].result == "approved"
        assert len(job.notifications) == 1
        assert job.notifications[0].event_type == "job_created"
        assert session.query(CommandLog).filter_by(command_name="create_job").one().result_status == "success"
        assert session.get(LlmCache, "outline:abc").response_payload["summary"] == "cached"
        assert session.query(PromptTemplate).filter_by(template_name="outline").one().is_active is True
