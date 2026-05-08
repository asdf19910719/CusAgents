from app.schemas.common import StrictSchema


class StoryReferenceAssetInput(StrictSchema):
    asset_type: str
    name: str
    description: str
    prompt: str
    file_path: str
    metadata_json: dict = {}


class StoryShotInput(StrictSchema):
    shot_index: int
    title: str
    script_text: str
    visual_description: str
    camera_motion: str
    character_names: list[str] = []
    scene_names: list[str] = []
    prop_names: list[str] = []
    duration: int = 5
    ratio: str = "16:9"
    shot_image_path: str | None = None
    metadata_json: dict = {}


class StoryVideoCreateRequest(StrictSchema):
    title: str
    source_text: str
    source_type: str = "outline"
    style_prompt: str = ""
    notification_target_id: str | None = None
    reference_assets: list[StoryReferenceAssetInput] = []
    shots: list[StoryShotInput] = []


class StoryVideoProjectResponse(StrictSchema):
    id: int
    title: str
    status: str
    current_stage: str
    shot_count: int
    reference_asset_count: int
    shot_image_count: int
