from app.schemas.common import StrictSchema


class PromptItem(StrictSchema):
    shot_index: int
    positive_prompt: str
    negative_prompt: str
    style_tags: list[str]
