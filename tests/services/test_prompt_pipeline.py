from app.schemas.storyboard import StoryboardShotList
from app.services.prompt_service import PromptAssemblyService, PromptTemplateService


def test_prompt_assembly_service_generates_one_prompt_per_shot():
    storyboard = StoryboardShotList.model_validate(
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
                },
                {
                    "shot_index": 2,
                    "scene": "屋檐下",
                    "subject": "仇人",
                    "action": "抬头冷笑",
                    "camera": "特写",
                    "lighting": "侧逆光",
                    "emotion": "挑衅",
                    "duration_hint": "2s",
                },
                {
                    "shot_index": 3,
                    "scene": "决斗现场",
                    "subject": "两人对峙",
                    "action": "拔刀",
                    "camera": "大全景",
                    "lighting": "晨雾逆光",
                    "emotion": "紧绷",
                    "duration_hint": "4s",
                },
            ]
        }
    )
    service = PromptAssemblyService(PromptTemplateService(template_root="app/templates"))

    prompts = service.build_prompts(storyboard, style_preset="cinematic", version="v1")

    assert len(prompts) == 3
    assert prompts[0].shot_index == 1
    assert "剑客" in prompts[0].positive_prompt
    assert "blurry" in prompts[0].negative_prompt
