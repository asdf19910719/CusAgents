---
name: commands
description: "Skill for the Commands area of CusAgents. 57 symbols across 10 files."
---

# Commands

57 symbols | 10 files | Cohesion: 77%

## When to Use

- Working with code in `tests/`
- Understanding how test_command_router_creates_codex_run_and_enqueues_it, test_command_router_creates_video_job_and_enqueues_it, test_command_router_can_query_codex_run_status work
- Modifying commands-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `app/commands/router.py` | CommandRouter, handle, _dispatch, _create_job, _job_status (+11) |
| `tests/commands/test_command_router.py` | FakeDispatcher, FakeNotificationService, test_command_router_creates_codex_run_and_enqueues_it, test_command_router_creates_video_job_and_enqueues_it, test_command_router_can_query_codex_run_status (+6) |
| `tests/commands/test_command_parser.py` | test_parse_create_command_with_quoted_topic, test_parse_status_command, test_parse_health_command_without_arguments, test_parse_video_command, test_parse_video_status_command (+6) |
| `tests/channels/test_feishu_long_connection.py` | FakeDispatcher, FakeNotificationService, _build_event, test_long_connection_handler_processes_text_message_and_sends_command_result, command_router_factory (+2) |
| `app/channels/feishu_long_connection.py` | handle_message_receive_v1, command_router_factory, _format_command_result_message |
| `app/commands/parser.py` | parse_command_text, _parse_arguments, _require |
| `tests/e2e/test_codex_conversation_flow.py` | FakeDispatcher, test_execute_codex_run_writes_assistant_message_back_to_conversation |
| `app/commands/schemas.py` | CommandRequest, CommandResult |
| `tests/e2e/test_worker_flow.py` | fake_load_settings |
| `app/core/config.py` | Settings |

## Entry Points

Start here when exploring this area:

- **`test_command_router_creates_codex_run_and_enqueues_it`** (Function) — `tests/commands/test_command_router.py:43`
- **`test_command_router_creates_video_job_and_enqueues_it`** (Function) — `tests/commands/test_command_router.py:79`
- **`test_command_router_can_query_codex_run_status`** (Function) — `tests/commands/test_command_router.py:111`
- **`test_command_router_treats_plain_text_as_codex_run`** (Function) — `tests/commands/test_command_router.py:151`
- **`test_command_router_resets_conversation_for_new_command`** (Function) — `tests/commands/test_command_router.py:181`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `FakeDispatcher` | Class | `tests/commands/test_command_router.py` | 9 |
| `FakeNotificationService` | Class | `tests/commands/test_command_router.py` | 27 |
| `TrackingConversationService` | Class | `tests/commands/test_command_router.py` | 237 |
| `TrackingRouter` | Class | `tests/commands/test_command_router.py` | 260 |
| `FakeDispatcher` | Class | `tests/channels/test_feishu_long_connection.py` | 8 |
| `FakeNotificationService` | Class | `tests/channels/test_feishu_long_connection.py` | 13 |
| `FakeDispatcher` | Class | `tests/e2e/test_codex_conversation_flow.py` | 14 |
| `Settings` | Class | `app/core/config.py` | 4 |
| `CommandRouter` | Class | `app/commands/router.py` | 15 |
| `CommandRequest` | Class | `app/commands/schemas.py` | 3 |
| `CommandResult` | Class | `app/commands/schemas.py` | 17 |
| `test_command_router_creates_codex_run_and_enqueues_it` | Function | `tests/commands/test_command_router.py` | 43 |
| `test_command_router_creates_video_job_and_enqueues_it` | Function | `tests/commands/test_command_router.py` | 79 |
| `test_command_router_can_query_codex_run_status` | Function | `tests/commands/test_command_router.py` | 111 |
| `test_command_router_treats_plain_text_as_codex_run` | Function | `tests/commands/test_command_router.py` | 151 |
| `test_command_router_resets_conversation_for_new_command` | Function | `tests/commands/test_command_router.py` | 181 |
| `test_command_router_allows_run_codex_without_chat_id` | Function | `tests/commands/test_command_router.py` | 205 |
| `test_command_router_uses_locked_conversation_access_for_chat_messages` | Function | `tests/commands/test_command_router.py` | 233 |
| `test_long_connection_handler_processes_text_message_and_sends_command_result` | Function | `tests/channels/test_feishu_long_connection.py` | 51 |
| `command_router_factory` | Function | `tests/channels/test_feishu_long_connection.py` | 60 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Mobile_job_detail → Settings` | cross_community | 5 |
| `Mobile_jobs_page → Settings` | cross_community | 5 |
| `Create_mobile_job → Settings` | cross_community | 5 |
| `Mobile_job_action → Settings` | cross_community | 5 |
| `Mobile_asset_preview → Settings` | cross_community | 5 |
| `Handle_message_receive_v1 → Settings` | cross_community | 5 |
| `Handle → Get` | cross_community | 5 |
| `Handle → ConversationService` | cross_community | 5 |
| `Handle → ConversationSession` | cross_community | 5 |
| `Handle → _serialize_time` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Services | 6 calls |
| Routes | 6 calls |
| Channels | 3 calls |
| Scripts | 2 calls |
| Models | 2 calls |
| Workers | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_command_router_creates_codex_run_and_enqueues_it"})` — see callers and callees
2. `gitnexus_query({query: "commands"})` — find related execution flows
3. Read key files listed above for implementation details
