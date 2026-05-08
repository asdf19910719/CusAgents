from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.asset import Asset
from app.db.models.job import Job
from app.schemas.prompt import PromptItem
from app.providers.image.base import ImageGenerationResult
from app.providers.image.dreamina_cli_client import DreaminaCliError
from app.services.image_service import ImageGenerationService


class FakeImageProvider:
    def __init__(self, provider_name="comfyui_remote", should_fail=False):
        self.provider_name = provider_name
        self.should_fail = should_fail
        self.calls = []

    def generate_image(self, shot_index, positive_prompt, negative_prompt, style_preset, seed):
        self.calls.append((shot_index, positive_prompt, negative_prompt, style_preset, seed))
        if self.should_fail:
            raise RuntimeError(self.provider_name + " submit failed")
        return ImageGenerationResult(
            provider_name=self.provider_name,
            remote_job_id=self.provider_name + "-job-" + str(shot_index),
            image_bytes=b"fake-image",
            file_name=self.provider_name + "-" + str(shot_index),
            file_extension=".png",
            metadata={"provider_name": self.provider_name, "seed": seed},
        )


def create_job(session):
    job = Job(
        request_id="req-image",
        topic="冷血剑客复仇",
        style_preset="cinematic",
        target_shot_count=2,
        image_backend="comfyui_remote",
        status="pending",
        idempotency_key="image-key",
        current_step="image",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def test_image_generation_service_creates_asset_records(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = ImageGenerationService(
        providers={
            "comfyui_remote": FakeImageProvider("comfyui_remote"),
            "third_party": FakeImageProvider("third_party"),
        },
        default_backend="comfyui_remote",
        output_dir=str(tmp_path),
    )
    prompts = [
        PromptItem(
            shot_index=1,
            positive_prompt="hero in rain",
            negative_prompt="blurry",
            style_tags=["cinematic"],
        ),
        PromptItem(
            shot_index=2,
            positive_prompt="villain under roof",
            negative_prompt="blurry",
            style_tags=["cinematic"],
        ),
    ]

    with Session(engine) as session:
        job = create_job(session)

        assets = service.generate_assets(session, job, prompts, "cinematic")

        saved_assets = session.execute(select(Asset).order_by(Asset.shot_index)).scalars().all()
        assert len(assets) == 2
        assert len(saved_assets) == 2
        assert saved_assets[0].status == "completed"
        assert saved_assets[0].workflow_json["provider_name"] == "comfyui_remote"
        assert Path(saved_assets[0].file_path).exists()


def test_image_generation_service_marks_failed_asset_on_exception(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = ImageGenerationService(
        providers={"comfyui_remote": FakeImageProvider("comfyui_remote", should_fail=True)},
        default_backend="comfyui_remote",
        output_dir=str(tmp_path),
    )
    prompts = [
        PromptItem(
            shot_index=1,
            positive_prompt="hero in rain",
            negative_prompt="blurry",
            style_tags=["cinematic"],
        )
    ]

    with Session(engine) as session:
        job = create_job(session)
        assets = service.generate_assets(session, job, prompts, "cinematic")

        assert len(assets) == 1
        assert assets[0].status == "failed"
        assert "submit failed" in assets[0].preview_path


def test_image_generation_service_can_switch_to_third_party_backend(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = ImageGenerationService(
        providers={
            "comfyui_remote": FakeImageProvider("comfyui_remote"),
            "third_party": FakeImageProvider("third_party"),
        },
        default_backend="comfyui_remote",
        output_dir=str(tmp_path),
    )
    prompts = [
        PromptItem(
            shot_index=1,
            positive_prompt="hero in rain",
            negative_prompt="blurry",
            style_tags=["cinematic"],
        )
    ]

    with Session(engine) as session:
        job = create_job(session)
        job.image_backend = "third_party"
        session.commit()

        assets = service.generate_assets(session, job, prompts, "cinematic")

        assert len(assets) == 1
        assert assets[0].workflow_json["provider_name"] == "third_party"
        assert "third_party-1.png" in assets[0].file_path


def test_image_generation_service_can_switch_to_codex_cli_backend(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = ImageGenerationService(
        providers={
            "comfyui_remote": FakeImageProvider("comfyui_remote"),
            "third_party": FakeImageProvider("third_party"),
            "codex_cli": FakeImageProvider("codex_cli"),
        },
        default_backend="comfyui_remote",
        output_dir=str(tmp_path),
    )
    prompts = [
        PromptItem(
            shot_index=1,
            positive_prompt="hero in rain",
            negative_prompt="blurry",
            style_tags=["cinematic"],
        )
    ]

    with Session(engine) as session:
        job = create_job(session)
        job.image_backend = "codex_cli"
        session.commit()

        assets = service.generate_assets(session, job, prompts, "cinematic")

        assert len(assets) == 1
        assert assets[0].workflow_json["provider_name"] == "codex_cli"
        assert "codex_cli-1.png" in assets[0].file_path


def test_image_generation_service_preserves_dreamina_submit_id_on_querying_failure(tmp_path):
    class QueryingDreaminaProvider:
        def generate_image(self, shot_index, positive_prompt, negative_prompt, style_preset, seed):
            raise DreaminaCliError(
                "dreamina cli text2image task is still querying; submit_id=submit-querying",
                submit_id="submit-querying",
                gen_status="querying",
                metadata={
                    "provider_name": "dreamina_cli",
                    "submit_id": "submit-querying",
                    "gen_status": "querying",
                    "command": ["dreamina", "text2image"],
                },
            )

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = ImageGenerationService(
        providers={"dreamina_cli": QueryingDreaminaProvider()},
        default_backend="dreamina_cli",
        output_dir=str(tmp_path),
    )
    prompts = [
        PromptItem(
            shot_index=1,
            positive_prompt="hero in rain",
            negative_prompt="blurry",
            style_tags=["cinematic"],
        )
    ]

    with Session(engine) as session:
        job = create_job(session)
        job.image_backend = "dreamina_cli"
        session.commit()

        assets = service.generate_assets(session, job, prompts, "cinematic")

        assert len(assets) == 1
        assert assets[0].status == "failed"
        assert assets[0].workflow_json["provider_name"] == "dreamina_cli"
        assert assets[0].workflow_json["submit_id"] == "submit-querying"
        assert assets[0].workflow_json["gen_status"] == "querying"
