---
name: models
description: "Skill for the Models area of CusAgents. 23 symbols across 18 files."
---

# Models

23 symbols | 18 files | Cohesion: 62%

## When to Use

- Working with code in `app/`
- Understanding how test_story_video_models_can_be_created_and_related, create_project, safe_enqueue_video work
- Modifying models-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `app/api/routes/videos.py` | safe_enqueue_video, create_video_job, retry_video_job |
| `app/api/routes/story_videos.py` | project_response, create_story_video_project, get_story_video_project |
| `tests/services/test_models.py` | test_story_video_models_can_be_created_and_related, test_core_models_can_be_created_and_related |
| `app/services/story_video_service.py` | create_project |
| `app/db/base.py` | Base |
| `app/db/models/video_job.py` | VideoJob |
| `app/db/models/story_shot_video_job.py` | StoryShotVideoJob |
| `app/db/models/story_shot_image.py` | StoryShotImage |
| `app/db/models/story_shot.py` | StoryShot |
| `app/db/models/story_reference_asset.py` | StoryReferenceAsset |

## Entry Points

Start here when exploring this area:

- **`test_story_video_models_can_be_created_and_related`** (Function) — `tests/services/test_models.py:162`
- **`create_project`** (Function) — `app/services/story_video_service.py:25`
- **`safe_enqueue_video`** (Function) — `app/api/routes/videos.py:30`
- **`create_video_job`** (Function) — `app/api/routes/videos.py:83`
- **`retry_video_job`** (Function) — `app/api/routes/videos.py:156`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `Base` | Class | `app/db/base.py` | 3 |
| `VideoJob` | Class | `app/db/models/video_job.py` | 6 |
| `StoryShotVideoJob` | Class | `app/db/models/story_shot_video_job.py` | 6 |
| `StoryShotImage` | Class | `app/db/models/story_shot_image.py` | 6 |
| `StoryShot` | Class | `app/db/models/story_shot.py` | 6 |
| `StoryReferenceAsset` | Class | `app/db/models/story_reference_asset.py` | 6 |
| `StoryProject` | Class | `app/db/models/story_project.py` | 6 |
| `StoryPipelineRun` | Class | `app/db/models/story_pipeline_run.py` | 6 |
| `StepRun` | Class | `app/db/models/step_run.py` | 8 |
| `PromptTemplate` | Class | `app/db/models/prompt_template.py` | 6 |
| `LlmCache` | Class | `app/db/models/llm_cache.py` | 6 |
| `CommandLog` | Class | `app/db/models/command_log.py` | 6 |
| `test_story_video_models_can_be_created_and_related` | Function | `tests/services/test_models.py` | 162 |
| `create_project` | Function | `app/services/story_video_service.py` | 25 |
| `safe_enqueue_video` | Function | `app/api/routes/videos.py` | 30 |
| `create_video_job` | Function | `app/api/routes/videos.py` | 83 |
| `retry_video_job` | Function | `app/api/routes/videos.py` | 156 |
| `project_response` | Function | `app/api/routes/story_videos.py` | 23 |
| `create_story_video_project` | Function | `app/api/routes/story_videos.py` | 50 |
| `get_story_video_project` | Function | `app/api/routes/story_videos.py` | 60 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Handle_message_receive_v1 → CommandLog` | cross_community | 4 |
| `Create_story_video_project → StoryProject` | intra_community | 3 |
| `Create_story_video_project → StoryReferenceAsset` | intra_community | 3 |
| `Create_story_video_project → StoryShot` | intra_community | 3 |
| `Create_story_video_project → StoryShotImage` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Routes | 4 calls |
| Services | 2 calls |
| Api | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_story_video_models_can_be_created_and_related"})` — see callers and callees
2. `gitnexus_query({query: "models"})` — find related execution flows
3. Read key files listed above for implementation details
