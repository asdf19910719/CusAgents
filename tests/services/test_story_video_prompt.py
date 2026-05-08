from app.services.story_video_prompt import (
    StoryVideoReferenceImage,
    build_story_video_prompt,
    limit_reference_images,
    select_video_mode,
)


def test_select_video_mode_uses_text2video_without_images():
    assert select_video_mode([], keyframe_sequence=False) == "text2video"


def test_select_video_mode_uses_image2video_for_one_image():
    image = StoryVideoReferenceImage(
        file_path="output/shot-001.png",
        file_name="shot-001.png",
        usage="当前分镜图",
        role="shot",
    )

    assert select_video_mode([image], keyframe_sequence=False) == "image2video"


def test_select_video_mode_uses_multimodal2video_for_multiple_images():
    images = [
        StoryVideoReferenceImage("output/shot-001.png", "shot-001.png", "当前分镜图", "shot"),
        StoryVideoReferenceImage("output/hero.png", "hero.png", "主角三视图", "character"),
    ]

    assert select_video_mode(images, keyframe_sequence=False) == "multimodal2video"


def test_select_video_mode_prefers_multiframe_for_keyframe_sequence():
    images = [
        StoryVideoReferenceImage("output/first.png", "first.png", "首帧", "first_frame"),
        StoryVideoReferenceImage("output/last.png", "last.png", "尾帧", "last_frame"),
    ]

    assert select_video_mode(images, keyframe_sequence=True) == "multiframe2video"


def test_build_story_video_prompt_includes_reference_file_names_and_usages():
    images = [
        StoryVideoReferenceImage("output/shot-001.png", "shot-001.png", "当前分镜图，作为构图和动作起点", "shot"),
        StoryVideoReferenceImage("output/hero.png", "hero.png", "主角三视图，保持服装一致", "character"),
    ]

    prompt = build_story_video_prompt(
        shot_index=1,
        script_text="主角在雨夜小巷中回头。",
        visual_description="霓虹灯反射在积水上。",
        camera_motion="低角度缓慢推近。",
        reference_images=images,
    )

    assert "分镜 001" in prompt
    assert "shot-001.png：当前分镜图，作为构图和动作起点" in prompt
    assert "hero.png：主角三视图，保持服装一致" in prompt
    assert "不要改变角色身份" in prompt


def test_limit_reference_images_keeps_shot_character_scene_prop_priority():
    images = [
        StoryVideoReferenceImage("output/extra.png", "extra.png", "辅助风格图", "style"),
        StoryVideoReferenceImage("output/prop.png", "prop.png", "关键物品", "prop"),
        StoryVideoReferenceImage("output/scene.png", "scene.png", "当前场景", "scene"),
        StoryVideoReferenceImage("output/hero.png", "hero.png", "出场主角", "character"),
        StoryVideoReferenceImage("output/shot.png", "shot.png", "当前分镜图", "shot"),
    ]

    limited = limit_reference_images(images, max_images=3)

    assert [image.file_name for image in limited] == ["shot.png", "hero.png", "scene.png"]
