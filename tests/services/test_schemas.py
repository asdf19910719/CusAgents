import pytest
from pydantic import ValidationError

from app.schemas.prompt import PromptItem
from app.schemas.storyboard import StoryboardShot, StoryboardShotList


def test_storyboard_schema_accepts_valid_shots():
    payload = StoryboardShotList(
        shots=[
            StoryboardShot(
                shot_index=1,
                scene="雨夜街巷",
                subject="剑客",
                action="缓步前行",
                camera="中景跟拍",
                lighting="冷色霓虹",
                emotion="压抑",
                duration_hint="3s",
            ),
            StoryboardShot(
                shot_index=2,
                scene="屋檐下",
                subject="仇人",
                action="抬头冷笑",
                camera="特写",
                lighting="侧逆光",
                emotion="挑衅",
                duration_hint="2s",
            ),
        ]
    )

    assert len(payload.shots) == 2
    assert payload.shots[0].shot_index == 1


def test_storyboard_schema_rejects_missing_required_fields():
    with pytest.raises(ValidationError):
        StoryboardShot(
            shot_index=1,
            scene="雨夜街巷",
            subject="剑客",
            action="缓步前行",
            camera="中景跟拍",
            lighting="冷色霓虹",
            emotion="压抑",
        )


def test_storyboard_schema_rejects_non_sequential_shot_indexes():
    with pytest.raises(ValidationError) as exc_info:
        StoryboardShotList(
            shots=[
                StoryboardShot(
                    shot_index=1,
                    scene="雨夜街巷",
                    subject="剑客",
                    action="缓步前行",
                    camera="中景跟拍",
                    lighting="冷色霓虹",
                    emotion="压抑",
                    duration_hint="3s",
                ),
                StoryboardShot(
                    shot_index=3,
                    scene="屋檐下",
                    subject="仇人",
                    action="抬头冷笑",
                    camera="特写",
                    lighting="侧逆光",
                    emotion="挑衅",
                    duration_hint="2s",
                ),
            ]
        )

    assert "sequential" in str(exc_info.value)


def test_prompt_schema_rejects_missing_required_fields():
    with pytest.raises(ValidationError):
        PromptItem(
            shot_index=1,
            positive_prompt="hero in rain",
            style_tags=["cinematic"],
        )
