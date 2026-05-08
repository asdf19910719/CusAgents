---
name: services
description: "Skill for the Services area of CusAgents. 237 symbols across 55 files."
---

# Services

237 symbols | 55 files | Cohesion: 79%

## When to Use

- Working with code in `app/`
- Understanding how test_conversation_models_can_be_created, test_conversation_service_reuses_active_session, test_conversation_service_rotates_expired_session work
- Modifying services-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `app/services/conversation_service.py` | ConversationService, get_or_create_session, append_message, build_resolved_prompt, compact_if_needed (+7) |
| `app/services/notification_service.py` | FeishuAppMessageNotifier, send_message, FeishuWebhookNotifier, NotificationService, notify_job_event (+7) |
| `tests/services/test_orchestration_service.py` | FakeOutlineService, FakeStoryboardService, FakePromptService, FakeImageService, FakeQualityService (+7) |
| `tests/services/test_notification_service.py` | create_job, build_transport, test_notification_service_records_sent_notification, test_notification_service_records_failed_notification, test_feishu_app_message_notifier_sends_message_to_chat_id (+6) |
| `tests/services/test_video_service.py` | FakeVideoProvider, FakeNotificationService, create_video_job, test_video_service_saves_video_asset_and_completes_job, test_video_service_uses_job_generation_parameters (+6) |
| `tests/services/test_conversation_service.py` | test_conversation_models_can_be_created, test_conversation_service_reuses_active_session, test_conversation_service_rotates_expired_session, test_conversation_service_builds_resolved_prompt_from_summary_and_recent_messages, test_conversation_service_compacts_old_messages_and_keeps_recent_ones (+3) |
| `tests/services/test_image_service.py` | FakeImageProvider, create_job, test_image_generation_service_creates_asset_records, test_image_generation_service_marks_failed_asset_on_exception, test_image_generation_service_can_switch_to_third_party_backend (+3) |
| `app/services/story_video_service.py` | _collect_reference_images, _reference_usage, _reference_role, StoryVideoService, submit_next_shot_video (+3) |
| `app/services/prompt_service.py` | PromptTemplateService, PromptAssemblyService, build_prompts, _template_name, _required_fields (+1) |
| `app/services/replay_guard_service.py` | InMemoryReplayStore, mark_seen, _cleanup, RedisReplayStore, _get_client (+1) |

## Entry Points

Start here when exploring this area:

- **`test_conversation_models_can_be_created`** (Function) — `tests/services/test_conversation_service.py:12`
- **`test_conversation_service_reuses_active_session`** (Function) — `tests/services/test_conversation_service.py:38`
- **`test_conversation_service_rotates_expired_session`** (Function) — `tests/services/test_conversation_service.py:54`
- **`test_conversation_service_builds_resolved_prompt_from_summary_and_recent_messages`** (Function) — `tests/services/test_conversation_service.py:70`
- **`test_conversation_service_compacts_old_messages_and_keeps_recent_ones`** (Function) — `tests/services/test_conversation_service.py:97`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `ConversationService` | Class | `app/services/conversation_service.py` | 9 |
| `ConversationSession` | Class | `app/db/models/conversation_session.py` | 6 |
| `ConversationMessage` | Class | `app/db/models/conversation_message.py` | 6 |
| `CodexRun` | Class | `app/db/models/codex_run.py` | 6 |
| `FeishuAppMessageNotifier` | Class | `app/services/notification_service.py` | 9 |
| `FeishuWebhookNotifier` | Class | `app/services/notification_service.py` | 107 |
| `NotificationService` | Class | `app/services/notification_service.py` | 124 |
| `OutboundNotification` | Class | `app/db/models/outbound_notification.py` | 6 |
| `FakeStoryboardProvider` | Class | `tests/services/test_storyboard_service.py` | 16 |
| `FakeOutlineProvider` | Class | `tests/e2e/test_full_pipeline.py` | 19 |
| `FakeStoryboardProvider` | Class | `tests/e2e/test_full_pipeline.py` | 31 |
| `FakeComfyClient` | Class | `tests/e2e/test_full_pipeline.py` | 58 |
| `StoryboardService` | Class | `app/services/storyboard_service.py` | 6 |
| `PromptTemplateService` | Class | `app/services/prompt_service.py` | 7 |
| `PromptAssemblyService` | Class | `app/services/prompt_service.py` | 30 |
| `CacheService` | Class | `app/services/cache_service.py` | 5 |
| `FakeVideoProvider` | Class | `tests/services/test_video_service.py` | 10 |
| `FakeNotificationService` | Class | `tests/services/test_video_service.py` | 49 |
| `FailingProvider` | Class | `tests/services/test_video_service.py` | 157 |
| `StructuredProvider` | Class | `tests/services/test_video_service.py` | 181 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Handle_feishu_events → Time_func` | intra_community | 5 |
| `Handle_feishu_events → _cleanup` | intra_community | 5 |
| `Handle_feishu_events → _get_client` | intra_community | 5 |
| `Handle_feishu_events → _build_key` | intra_community | 5 |
| `Get_runtime_health → FakeResult` | cross_community | 5 |
| `Get_runtime_health → Get` | cross_community | 5 |
| `Submit_next_story_video → FakeResult` | cross_community | 5 |
| `Submit_next_story_video → Get` | cross_community | 5 |
| `Resume_story_video_project → FakeResult` | cross_community | 5 |
| `Resume_story_video_project → Get` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Routes | 26 calls |
| Models | 11 calls |
| Commands | 10 calls |
| Scripts | 5 calls |
| Api | 2 calls |
| Providers | 2 calls |
| Image | 2 calls |
| Video | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_conversation_models_can_be_created"})` — see callers and callees
2. `gitnexus_query({query: "services"})` — find related execution flows
3. Read key files listed above for implementation details
