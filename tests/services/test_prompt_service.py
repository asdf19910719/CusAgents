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


def test_prompt_template_service_rejects_missing_context_fields():
    service = PromptTemplateService(template_root="app/templates")

    with pytest.raises(ValueError) as exc_info:
        service.render(
            step_name="outline",
            version="v1",
            context={"topic": "冷血剑客复仇"},
        )

    assert "style_preset" in str(exc_info.value)
