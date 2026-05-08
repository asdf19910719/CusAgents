---
name: api
description: "Skill for the Api area of CusAgents. 44 symbols across 7 files."
---

# Api

44 symbols | 7 files | Cohesion: 92%

## When to Use

- Working with code in `tests/`
- Understanding how test_mobile_can_create_job_and_redirect_to_detail, test_mobile_can_create_dreamina_cli_job_and_redirect_to_detail, test_mobile_can_create_codex_cli_job_and_redirect_to_detail work
- Modifying api-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/api/test_mobile_api.py` | FakeDispatcher, FakeNotificationService, test_mobile_can_create_job_and_redirect_to_detail, test_mobile_can_create_dreamina_cli_job_and_redirect_to_detail, test_mobile_can_create_codex_cli_job_and_redirect_to_detail (+4) |
| `tests/api/test_videos_api.py` | test_refresh_video_job_queries_saved_submit_id, FakeRecoveryService, test_refresh_video_job_saves_asset_when_query_succeeds, FakeNotificationService, test_video_job_can_stay_querying_for_long_running_tasks (+4) |
| `tests/api/test_jobs_api.py` | test_create_job_enqueues_when_dispatcher_is_overridden, FakeDispatcher, test_create_job_sends_notification_when_notification_service_is_overridden, FakeNotificationService, test_retry_job_reenqueues_when_dispatcher_is_overridden (+3) |
| `tests/api/test_webhooks_api.py` | test_feishu_event_callback_can_create_job_from_text_command, FakeDispatcher, FakeNotificationService, test_feishu_event_callback_can_query_job_status, test_feishu_event_callback_can_reset_conversation (+2) |
| `tests/api/test_story_videos_api.py` | FakeStoryVideoDispatcher, story_project_payload, test_create_and_get_story_video_project, test_submit_next_story_shot_video, test_resume_story_project_advances_after_completed_video_job (+2) |
| `tests/api/test_admin_api.py` | test_admin_conversations_endpoint_returns_conversation_overviews, FakeConversationService, test_admin_conversation_cleanup_endpoint_returns_cleanup_result |
| `app/db/models/asset.py` | Asset |

## Entry Points

Start here when exploring this area:

- **`test_mobile_can_create_job_and_redirect_to_detail`** (Function) — `tests/api/test_mobile_api.py:32`
- **`test_mobile_can_create_dreamina_cli_job_and_redirect_to_detail`** (Function) — `tests/api/test_mobile_api.py:56`
- **`test_mobile_can_create_codex_cli_job_and_redirect_to_detail`** (Function) — `tests/api/test_mobile_api.py:80`
- **`test_mobile_can_create_chatgpt_web_job_and_redirect_to_detail`** (Function) — `tests/api/test_mobile_api.py:104`
- **`test_mobile_job_detail_page_shows_job_state`** (Function) — `tests/api/test_mobile_api.py:128`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `FakeDispatcher` | Class | `tests/api/test_mobile_api.py` | 9 |
| `FakeNotificationService` | Class | `tests/api/test_mobile_api.py` | 14 |
| `Asset` | Class | `app/db/models/asset.py` | 6 |
| `FakeDispatcher` | Class | `tests/api/test_webhooks_api.py` | 26 |
| `FakeNotificationService` | Class | `tests/api/test_webhooks_api.py` | 30 |
| `FakeStoryVideoDispatcher` | Class | `tests/api/test_story_videos_api.py` | 7 |
| `FakeRecoveryService` | Class | `tests/api/test_story_videos_api.py` | 141 |
| `FakeRecoveryService` | Class | `tests/api/test_videos_api.py` | 111 |
| `FakeNotificationService` | Class | `tests/api/test_videos_api.py` | 159 |
| `FakeDispatcher` | Class | `tests/api/test_jobs_api.py` | 100 |
| `FakeNotificationService` | Class | `tests/api/test_jobs_api.py` | 136 |
| `FakeVideoDispatcher` | Class | `tests/api/test_videos_api.py` | 6 |
| `FailingDispatcher` | Class | `tests/api/test_jobs_api.py` | 229 |
| `FakeConversationService` | Class | `tests/api/test_admin_api.py` | 50 |
| `test_mobile_can_create_job_and_redirect_to_detail` | Function | `tests/api/test_mobile_api.py` | 32 |
| `test_mobile_can_create_dreamina_cli_job_and_redirect_to_detail` | Function | `tests/api/test_mobile_api.py` | 56 |
| `test_mobile_can_create_codex_cli_job_and_redirect_to_detail` | Function | `tests/api/test_mobile_api.py` | 80 |
| `test_mobile_can_create_chatgpt_web_job_and_redirect_to_detail` | Function | `tests/api/test_mobile_api.py` | 104 |
| `test_mobile_job_detail_page_shows_job_state` | Function | `tests/api/test_mobile_api.py` | 128 |
| `test_mobile_job_action_can_approve_and_redirect` | Function | `tests/api/test_mobile_api.py` | 154 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Routes | 6 calls |

## How to Explore

1. `gitnexus_context({name: "test_mobile_can_create_job_and_redirect_to_detail"})` — see callers and callees
2. `gitnexus_query({query: "api"})` — find related execution flows
3. Read key files listed above for implementation details
