from dataclasses import dataclass


@dataclass
class StoryVideoReferenceImage:
    file_path: str
    file_name: str
    usage: str
    role: str

    def to_manifest_item(self):
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "usage": self.usage,
            "role": self.role,
        }


ROLE_PRIORITY = {
    "shot": 0,
    "first_frame": 0,
    "last_frame": 1,
    "character": 2,
    "character_turnaround": 2,
    "scene": 3,
    "prop": 4,
    "style": 5,
}


def limit_reference_images(reference_images, max_images=None):
    sorted_images = sorted(
        reference_images,
        key=lambda image: (ROLE_PRIORITY.get(image.role, 99), image.file_name),
    )
    if max_images is None or max_images <= 0:
        return sorted_images
    return sorted_images[:max_images]


def select_video_mode(reference_images, keyframe_sequence=False):
    if keyframe_sequence:
        return "multiframe2video"
    count = len(reference_images)
    if count == 0:
        return "text2video"
    if count == 1:
        return "image2video"
    return "multimodal2video"


def build_reference_manifest(reference_images, max_images=None):
    selected = limit_reference_images(reference_images, max_images=max_images)
    dropped = [image for image in reference_images if image not in selected]
    return {
        "images": [image.to_manifest_item() for image in selected],
        "dropped_images": [image.to_manifest_item() for image in dropped],
    }


def build_story_video_prompt(shot_index, script_text, visual_description, camera_motion, reference_images):
    lines = [
        "分镜 {0:03d}：".format(int(shot_index)),
        script_text,
        "",
        "画面描述：",
        visual_description,
        "",
        "镜头运动：",
        camera_motion,
    ]
    if reference_images:
        lines.extend(["", "参考图清单："])
        for image in reference_images:
            lines.append("- {0}：{1}".format(image.file_name, image.usage))
        lines.extend(
            [
                "",
                "视频要求：",
                "请根据上述参考图生成本分镜视频。保持角色身份、服装、场景结构和关键道具外观一致。",
                "不要改变角色身份，不要新增未出现的主要角色，不要改变关键服装颜色和场景结构。",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "视频要求：",
                "请根据分镜文字生成本分镜视频，镜头运动要平稳，画面风格保持一致。",
            ]
        )
    return "\n".join(lines)
