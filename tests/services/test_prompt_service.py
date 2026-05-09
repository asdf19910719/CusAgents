import pytest

from app.services.prompt_service import PromptTemplateService


def test_prompt_template_service_renders_outline_template():
    service = PromptTemplateService(template_root="app/templates")

    rendered = service.render(
        step_name="outline",
        version="v1",
        context={
            "topic": "冷血剑客复仇",
            "style_preset": "cinematic",
            "target_shot_count": 8,
        },
    )

    assert "冷血剑客复仇" in rendered
    assert "cinematic" in rendered
    assert "8" in rendered


def test_prompt_template_service_allows_model_to_choose_shot_count():
    service = PromptTemplateService(template_root="app/templates")

    outline = service.render(
        step_name="outline",
        version="v1",
        context={
            "topic": "Guangxu merchant trapped in a ruined mountain temple",
            "style_preset": "cinematic Qing dynasty folk horror",
            "target_shot_count": 0,
        },
    )
    storyboard = service.render(
        step_name="storyboard",
        version="v1",
        context={
            "topic": "Guangxu merchant trapped in a ruined mountain temple",
            "style_preset": "cinematic Qing dynasty folk horror",
            "target_shot_count": 0,
            "outline_text": "A merchant meets a shapeshifting mountain spirit.",
        },
    )

    assert "Choose the number of storyboard shots" in outline
    assert "Choose the number of storyboard shots" in storyboard
    assert "into 0 storyboard shots" not in storyboard


def test_prompt_template_service_preserves_source_story_facts():
    service = PromptTemplateService(template_root="app/templates")

    outline = service.render(
        step_name="outline",
        version="v1",
        context={
            "topic": "光绪二十三年，徽州贩货人王二在破庙遇见山老，山老其实是山魈。",
            "style_preset": "cinematic Qing dynasty folk horror",
            "target_shot_count": 0,
        },
    )
    storyboard = service.render(
        step_name="storyboard",
        version="v1",
        context={
            "topic": "光绪二十三年，徽州贩货人王二在破庙遇见山老，山老其实是山魈。",
            "style_preset": "cinematic Qing dynasty folk horror",
            "target_shot_count": 0,
            "outline_text": "王二在暴雨夜进入荒废破庙，与山老同宿，夜半发现山老是山魈。",
        },
    )

    assert "Preserve the provided story facts" in outline
    assert "Preserve the provided story facts" in storyboard
    assert "Do not rename characters" in outline
    assert "Do not add new main characters" in storyboard


def test_prompt_template_service_rejects_missing_context_fields():
    service = PromptTemplateService(template_root="app/templates")

    with pytest.raises(ValueError) as exc_info:
        service.render(
            step_name="outline",
            version="v1",
            context={"topic": "冷血剑客复仇"},
        )

    assert "style_preset" in str(exc_info.value)
