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
from app.db.models.video_job import VideoJob


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


def test_video_notifications_can_attach_to_video_jobs():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        video_job = VideoJob(
            request_id="video-req-1",
            topic="city sunrise",
            prompt="cinematic city sunrise",
            backend="dreamina_video_cli",
            mode="text2video",
            status="completed",
            current_step="completed",
            duration=4,
            ratio="16:9",
            video_resolution="720p",
            model_version="seedance2.0",
        )
        notification = OutboundNotification(
            video_job=video_job,
            channel_type="feishu",
            target_id="chat-456",
            event_type="video_job_completed",
            payload_json={"message": "video done"},
            status="sent",
            retry_count=0,
        )
        session.add_all([video_job, notification])
        session.commit()
        session.refresh(video_job)

        assert len(video_job.notifications) == 1
        assert video_job.notifications[0].event_type == "video_job_completed"
        assert video_job.notifications[0].video_job_id == video_job.id


def test_story_video_models_can_be_created_and_related():
    from app.db.models.story_pipeline_run import StoryPipelineRun
    from app.db.models.story_project import StoryProject
    from app.db.models.story_reference_asset import StoryReferenceAsset
    from app.db.models.story_shot import StoryShot
    from app.db.models.story_shot_image import StoryShotImage
    from app.db.models.story_shot_video_job import StoryShotVideoJob

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        project = StoryProject(
            request_id="story-project-1",
            title="雨夜剑客",
            source_type="outline",
            source_text="一个剑客在雨夜寻找真相",
            style_prompt="cinematic noir",
            status="generating_videos",
            current_stage="video",
            notification_target_id="chat-story",
        )
        session.add(project)
        session.flush()

        reference = StoryReferenceAsset(
            project_id=project.id,
            asset_type="character_turnaround",
            name="hero",
            description="黑衣剑客三视图",
            prompt="hero turnaround sheet",
            image_asset_id=None,
            file_path="output/hero.png",
            status="completed",
            metadata_json={"priority": 1},
        )
        shot = StoryShot(
            project_id=project.id,
            shot_index=1,
            title="雨夜回头",
            script_text="主角在雨夜小巷中回头。",
            visual_description="neon alley rain",
            camera_motion="slow push in",
            character_names=["hero"],
            scene_names=["alley"],
            prop_names=["sword"],
            duration=5,
            ratio="16:9",
            status="ready",
            metadata_json={"scene": "alley"},
        )
        video_job = VideoJob(
            request_id="story-video-1",
            topic="雨夜剑客",
            prompt="video prompt",
            backend="dreamina_video_cli",
            mode="multimodal2video",
            status="querying",
            current_step="query_result",
            duration=5,
            ratio="16:9",
            video_resolution="720p",
            model_version="seedance2.0",
            submit_id="submit-story-1",
        )
        session.add_all([reference, shot, video_job])
        session.flush()

        shot_image = StoryShotImage(
            project_id=project.id,
            shot_id=shot.id,
            image_asset_id=None,
            file_path="output/shot-001.png",
            image_type="shot",
            prompt="shot image prompt",
            status="completed",
            metadata_json={"source": "generated"},
        )
        shot_video_job = StoryShotVideoJob(
            project_id=project.id,
            shot_id=shot.id,
            video_job_id=video_job.id,
            mode="multimodal2video",
            submit_id="submit-story-1",
            status="querying",
            reference_manifest_json={"images": [{"file_name": "shot-001.png"}]},
            prompt="video prompt",
            metadata_json={"attempt": 1},
        )
        run = StoryPipelineRun(
            project_id=project.id,
            run_type="full_auto",
            status="running",
            checkpoint_json={"current_shot_index": 1},
            error_message=None,
        )
        session.add_all([shot_image, shot_video_job, run])
        session.commit()
        session.refresh(project)

        assert project.id is not None
        assert len(project.reference_assets) == 1
        assert project.reference_assets[0].name == "hero"
        assert len(project.shots) == 1
        assert project.shots[0].character_names == ["hero"]
        assert len(project.shot_images) == 1
        assert project.shot_images[0].file_path.endswith("shot-001.png")
        assert len(project.shot_video_jobs) == 1
        assert project.shot_video_jobs[0].video_job.submit_id == "submit-story-1"
        assert len(project.pipeline_runs) == 1
        assert project.pipeline_runs[0].checkpoint_json["current_shot_index"] == 1
