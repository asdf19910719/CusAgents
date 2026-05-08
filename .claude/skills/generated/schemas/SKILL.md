---
name: schemas
description: "Skill for the Schemas area of CusAgents. 7 symbols across 5 files."
---

# Schemas

7 symbols | 5 files | Cohesion: 75%

## When to Use

- Working with code in `app/`
- Understanding how VideoCreateRequest, StoryReferenceAssetInput, StoryShotInput work
- Modifying schemas-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `app/schemas/story_video.py` | StoryReferenceAssetInput, StoryShotInput, StoryVideoProjectResponse |
| `app/schemas/video.py` | VideoCreateRequest |
| `app/schemas/review.py` | ReviewDecision |
| `app/schemas/job.py` | JobCreateRequest |
| `app/schemas/common.py` | StrictSchema |

## Entry Points

Start here when exploring this area:

- **`VideoCreateRequest`** (Class) — `app/schemas/video.py:5`
- **`StoryReferenceAssetInput`** (Class) — `app/schemas/story_video.py:3`
- **`StoryShotInput`** (Class) — `app/schemas/story_video.py:12`
- **`StoryVideoProjectResponse`** (Class) — `app/schemas/story_video.py:37`
- **`ReviewDecision`** (Class) — `app/schemas/review.py:5`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `VideoCreateRequest` | Class | `app/schemas/video.py` | 5 |
| `StoryReferenceAssetInput` | Class | `app/schemas/story_video.py` | 3 |
| `StoryShotInput` | Class | `app/schemas/story_video.py` | 12 |
| `StoryVideoProjectResponse` | Class | `app/schemas/story_video.py` | 37 |
| `ReviewDecision` | Class | `app/schemas/review.py` | 5 |
| `JobCreateRequest` | Class | `app/schemas/job.py` | 5 |
| `StrictSchema` | Class | `app/schemas/common.py` | 3 |

## How to Explore

1. `gitnexus_context({name: "VideoCreateRequest"})` — see callers and callees
2. `gitnexus_query({query: "schemas"})` — find related execution flows
3. Read key files listed above for implementation details
