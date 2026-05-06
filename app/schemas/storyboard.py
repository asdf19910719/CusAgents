from pydantic import Field, model_validator

from app.schemas.common import StrictSchema


class StoryboardShot(StrictSchema):
    shot_index: int = Field(ge=1)
    scene: str
    subject: str
    action: str
    camera: str
    lighting: str
    emotion: str
    duration_hint: str


class StoryboardShotList(StrictSchema):
    shots: list[StoryboardShot]

    @model_validator(mode="after")
    def validate_shot_indexes(self):
        expected_indexes = list(range(1, len(self.shots) + 1))
        actual_indexes = [shot.shot_index for shot in self.shots]
        if actual_indexes != expected_indexes:
            raise ValueError("shot indexes must be sequential starting at 1")
        return self
