from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.enums import JobStatus
from app.db.base import Base
from app.db.models.job import Job
from app.providers.llm.base import StructuredGenerationResult, TextGenerationResult
from app.providers.image.base import ImageGenerationResult
from app.services.cache_service import CacheService
from app.services.image_service import ImageGenerationService
from app.services.orchestration_service import OrchestrationService
from app.services.outline_service import OutlineService
from app.services.prompt_service import PromptAssemblyService, PromptTemplateService
from app.services.quality_service import QualityService
from app.services.storyboard_service import StoryboardService


class FakeOutlineProvider:
    def generate_text(self, prompt, model=None):
        return TextGenerationResult(
            content="一个剑客在雨夜追寻仇敌，最终逼近决战。",
            input_tokens=100,
            output_tokens=80,
            total_tokens=180,
            cost=Decimal("0.0100"),
            raw_response={"prompt": prompt},
        )


class FakeStoryboardProvider:
    def generate_structured(self, prompt, schema, model=None):
        payload = {
            "shots": [
                {
                    "shot_index": 1,
                    "scene": "雨夜街巷",
                    "subject": "剑客",
                    "action": "缓步前行",
                    "camera": "中景跟拍",
                    "lighting": "冷色霓虹",
                    "emotion": "压抑",
                    "duration_hint": "3s",
                }
            ]
        }
        return StructuredGenerationResult(
            parsed=schema.model_validate(payload),
            content=str(payload),
            input_tokens=120,
            output_tokens=90,
            total_tokens=210,
            cost=Decimal("0.0200"),
            raw_response={"prompt": prompt},
        )


class FakeComfyClient:
    def generate_image(self, shot_index, positive_prompt, negative_prompt, style_preset, seed):
        return ImageGenerationResult(
            provider_name="comfyui_remote",
            remote_job_id="prompt-1",
            image_bytes=b"fake-image",
            file_name="shot-1",
            file_extension=".png",
            metadata={"provider_name": "comfyui_remote", "seed": seed},
        )


def test_full_pipeline_runs_to_waiting_review(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    prompt_service = PromptTemplateService(template_root="app/templates")
    cache_service = CacheService()
    outline_service = OutlineService(FakeOutlineProvider(), prompt_service, cache_service)
    storyboard_service = StoryboardService(FakeStoryboardProvider(), prompt_service, cache_service)
    prompt_assembly_service = PromptAssemblyService(prompt_service)
    image_service = ImageGenerationService(
        providers={"comfyui_remote": FakeComfyClient()},
        default_backend="comfyui_remote",
        output_dir=str(tmp_path),
    )
    quality_service = QualityService()
    orchestration_service = OrchestrationService(
        outline_service=outline_service,
        storyboard_service=storyboard_service,
        prompt_service=prompt_assembly_service,
        image_service=image_service,
        quality_service=quality_service,
    )

    with Session(engine) as session:
        job = Job(
            request_id="req-full",
            topic="冷血剑客复仇",
            style_preset="cinematic",
            target_shot_count=1,
            status=JobStatus.PENDING,
            idempotency_key="full-key",
            current_step="outline",
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        result = orchestration_service.run_job(session, job, model_name="gpt-4.1-mini")

        assert result.status == JobStatus.WAITING_REVIEW
        assert result.current_step == "review"
