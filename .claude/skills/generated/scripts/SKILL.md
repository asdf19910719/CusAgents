---
name: scripts
description: "Skill for the Scripts area of CusAgents. 21 symbols across 12 files."
---

# Scripts

21 symbols | 12 files | Cohesion: 69%

## When to Use

- Working with code in `app/`
- Understanding how parse_args, main, parse_args work
- Modifying scripts-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/scripts/test_script_entrypoints.py` | run_python_script, test_run_feishu_long_connection_script_supports_check_mode, test_run_worker_script_supports_check_mode, test_run_chatgpt_web_login_script_supports_check_mode, test_run_chatgpt_web_browser_script_supports_check_mode |
| `scripts/run_chatgpt_web_browser.py` | parse_args, is_cdp_ready, main |
| `app/workers/jobs.py` | execute_codex_run, CodexAssetPreview, run_configured_codex_run |
| `scripts/run_chatgpt_web_login.py` | parse_args, main |
| `tests/commands/test_command_router.py` | __init__ |
| `app/core/config.py` | load_settings |
| `app/services/factory.py` | build_notification_service |
| `app/services/codex_run_service.py` | encode_image_paths |
| `app/commands/router.py` | __init__ |
| `app/api/routes/webhooks.py` | get_command_router |

## Entry Points

Start here when exploring this area:

- **`parse_args`** (Function) — `scripts/run_chatgpt_web_login.py:11`
- **`main`** (Function) — `scripts/run_chatgpt_web_login.py:21`
- **`parse_args`** (Function) — `scripts/run_chatgpt_web_browser.py:15`
- **`is_cdp_ready`** (Function) — `scripts/run_chatgpt_web_browser.py:25`
- **`main`** (Function) — `scripts/run_chatgpt_web_browser.py:33`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `CodexAssetPreview` | Class | `app/workers/jobs.py` | 86 |
| `parse_args` | Function | `scripts/run_chatgpt_web_login.py` | 11 |
| `main` | Function | `scripts/run_chatgpt_web_login.py` | 21 |
| `parse_args` | Function | `scripts/run_chatgpt_web_browser.py` | 15 |
| `is_cdp_ready` | Function | `scripts/run_chatgpt_web_browser.py` | 25 |
| `main` | Function | `scripts/run_chatgpt_web_browser.py` | 33 |
| `execute_codex_run` | Function | `app/workers/jobs.py` | 39 |
| `run_configured_codex_run` | Function | `app/workers/jobs.py` | 121 |
| `load_settings` | Function | `app/core/config.py` | 79 |
| `build_notification_service` | Function | `app/services/factory.py` | 95 |
| `encode_image_paths` | Function | `app/services/codex_run_service.py` | 92 |
| `get_command_router` | Function | `app/api/routes/webhooks.py` | 20 |
| `get_video_notification_service` | Function | `app/api/routes/videos.py` | 26 |
| `get_notification_service` | Function | `app/api/routes/jobs.py` | 24 |
| `run_python_script` | Function | `tests/scripts/test_script_entrypoints.py` | 9 |
| `test_run_feishu_long_connection_script_supports_check_mode` | Function | `tests/scripts/test_script_entrypoints.py` | 24 |
| `test_run_worker_script_supports_check_mode` | Function | `tests/scripts/test_script_entrypoints.py` | 38 |
| `test_run_chatgpt_web_login_script_supports_check_mode` | Function | `tests/scripts/test_script_entrypoints.py` | 66 |
| `test_run_chatgpt_web_browser_script_supports_check_mode` | Function | `tests/scripts/test_script_entrypoints.py` | 78 |
| `__init__` | Function | `tests/commands/test_command_router.py` | 10 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Mobile_job_detail → Settings` | cross_community | 5 |
| `Mobile_jobs_page → Settings` | cross_community | 5 |
| `Create_mobile_job → Settings` | cross_community | 5 |
| `Mobile_job_action → Settings` | cross_community | 5 |
| `Mobile_asset_preview → Settings` | cross_community | 5 |
| `Run_configured_codex_run → _is_image_file` | cross_community | 5 |
| `Handle_message_receive_v1 → Settings` | cross_community | 5 |
| `Mobile_login → Settings` | cross_community | 4 |
| `Run_configured_codex_run → Settings` | cross_community | 4 |
| `Get_video_dispatcher → Settings` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Services | 7 calls |
| Commands | 2 calls |
| Routes | 1 calls |

## How to Explore

1. `gitnexus_context({name: "parse_args"})` — see callers and callees
2. `gitnexus_query({query: "scripts"})` — find related execution flows
3. Read key files listed above for implementation details
