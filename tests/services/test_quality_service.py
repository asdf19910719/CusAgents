from app.schemas.prompt import PromptItem
from app.schemas.storyboard import StoryboardShotList
from app.services.quality_service import QualityService


def build_storyboard():
    return StoryboardShotList.model_validate(
        {
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
    )


def test_quality_service_passes_valid_inputs():
    service = QualityService()
    prompts = [
        PromptItem(
            shot_index=1,
            positive_prompt="hero in rain",
            negative_prompt="blurry",
            style_tags=["cinematic"],
        )
    ]
    assets = [{"shot_index": 1, "status": "completed"}]

    result = service.validate_generation(build_storyboard(), prompts, assets)

    assert result.result == "passed"


def test_quality_service_rejects_mismatched_asset_count():
    service = QualityService()
    prompts = [
        PromptItem(
            shot_index=1,
            positive_prompt="hero in rain",
            negative_prompt="blurry",
            style_tags=["cinematic"],
        )
    ]

    result = service.validate_generation(build_storyboard(), prompts, [])

    assert result.result == "failed"
    assert "asset count" in result.notes


def test_quality_service_rejects_failed_asset_status():
    service = QualityService()
    prompts = [
        PromptItem(
            shot_index=1,
            positive_prompt="hero in rain",
            negative_prompt="blurry",
            style_tags=["cinematic"],
        )
    ]
    assets = [{"shot_index": 1, "status": "failed"}]

    result = service.validate_generation(build_storyboard(), prompts, assets)

    assert result.result == "failed"
    assert "asset generation failed" in result.notes


def test_quality_service_allows_approval_and_rejection_transitions():
    service = QualityService()

    approved = service.build_manual_review(result="approved", notes="ok", reviewed_by="tester")
    rejected = service.build_manual_review(result="rejected", notes="redo", reviewed_by="tester")

    assert approved.result == "approved"
    assert rejected.result == "rejected"
