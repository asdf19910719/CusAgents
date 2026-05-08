---
name: routes
description: "Skill for the Routes area of CusAgents. 45 symbols across 14 files."
---

# Routes

45 symbols | 14 files | Cohesion: 61%

## When to Use

- Working with code in `app/`
- Understanding how handler, test_mobile_jobs_page_redirects_to_login_when_access_token_is_configured, test_mobile_logout_clears_session work
- Modifying routes-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `app/api/routes/mobile.py` | _page, _parse_form_body, _job_summary, _build_mobile_session_value, _has_valid_mobile_session (+11) |
| `app/api/routes/videos.py` | get_video_job, cancel_video_job, list_video_assets, resolve_video_result_path, save_refreshed_video_asset (+2) |
| `app/api/routes/jobs.py` | safe_enqueue, create_job, get_job, retry_job, approve_job (+2) |
| `tests/api/test_mobile_api.py` | test_mobile_jobs_page_redirects_to_login_when_access_token_is_configured, test_mobile_logout_clears_session |
| `app/api/routes/assets.py` | get_asset, get_job_assets |
| `tests/services/test_runtime_health_service.py` | FakeResult, execute |
| `app/services/video_notification_messages.py` | build_video_completion_message, build_video_failure_message |
| `tests/services/test_notification_service.py` | handler |
| `app/services/cache_service.py` | get |
| `app/db/models/review.py` | Review |

## Entry Points

Start here when exploring this area:

- **`handler`** (Function) — `tests/services/test_notification_service.py:35`
- **`test_mobile_jobs_page_redirects_to_login_when_access_token_is_configured`** (Function) — `tests/api/test_mobile_api.py:185`
- **`test_mobile_logout_clears_session`** (Function) — `tests/api/test_mobile_api.py:224`
- **`get`** (Function) — `app/services/cache_service.py:16`
- **`get_video_job`** (Function) — `app/api/routes/videos.py:116`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `Review` | Class | `app/db/models/review.py` | 8 |
| `FakeResult` | Class | `tests/services/test_runtime_health_service.py` | 4 |
| `VideoAsset` | Class | `app/db/models/video_asset.py` | 6 |
| `handler` | Function | `tests/services/test_notification_service.py` | 35 |
| `test_mobile_jobs_page_redirects_to_login_when_access_token_is_configured` | Function | `tests/api/test_mobile_api.py` | 185 |
| `test_mobile_logout_clears_session` | Function | `tests/api/test_mobile_api.py` | 224 |
| `get` | Function | `app/services/cache_service.py` | 16 |
| `get_video_job` | Function | `app/api/routes/videos.py` | 116 |
| `cancel_video_job` | Function | `app/api/routes/videos.py` | 174 |
| `mobile_jobs_page` | Function | `app/api/routes/mobile.py` | 244 |
| `mobile_login_page` | Function | `app/api/routes/mobile.py` | 303 |
| `mobile_login` | Function | `app/api/routes/mobile.py` | 325 |
| `create_mobile_job` | Function | `app/api/routes/mobile.py` | 356 |
| `mobile_job_detail` | Function | `app/api/routes/mobile.py` | 406 |
| `mobile_job_action` | Function | `app/api/routes/mobile.py` | 478 |
| `mobile_asset_preview` | Function | `app/api/routes/mobile.py` | 520 |
| `safe_enqueue` | Function | `app/api/routes/jobs.py` | 29 |
| `create_job` | Function | `app/api/routes/jobs.py` | 46 |
| `get_job` | Function | `app/api/routes/jobs.py` | 85 |
| `retry_job` | Function | `app/api/routes/jobs.py` | 118 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Mobile_job_detail → Settings` | cross_community | 5 |
| `Mobile_jobs_page → Settings` | cross_community | 5 |
| `Create_mobile_job → Settings` | cross_community | 5 |
| `Mobile_job_action → Settings` | cross_community | 5 |
| `Get_runtime_health → FakeResult` | cross_community | 5 |
| `Get_runtime_health → Get` | cross_community | 5 |
| `Submit_next_story_video → FakeResult` | cross_community | 5 |
| `Submit_next_story_video → Get` | cross_community | 5 |
| `Resume_story_video_project → FakeResult` | cross_community | 5 |
| `Resume_story_video_project → Get` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Services | 5 calls |
| Scripts | 2 calls |

## How to Explore

1. `gitnexus_context({name: "handler"})` — see callers and callees
2. `gitnexus_query({query: "routes"})` — find related execution flows
3. Read key files listed above for implementation details
