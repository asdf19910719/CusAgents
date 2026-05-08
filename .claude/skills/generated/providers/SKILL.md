---
name: providers
description: "Skill for the Providers area of CusAgents. 47 symbols across 12 files."
---

# Providers

47 symbols | 12 files | Cohesion: 87%

## When to Use

- Working with code in `tests/`
- Understanding how test_dreamina_cli_client_invokes_text2image_and_returns_output_path, test_dreamina_cli_client_raises_clear_error_when_generation_fails, test_dreamina_cli_client_keeps_submit_id_when_task_is_still_querying work
- Modifying providers-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/providers/test_dreamina_cli_provider.py` | FakeRunner, test_dreamina_cli_client_invokes_text2image_and_returns_output_path, test_dreamina_cli_client_raises_clear_error_when_generation_fails, test_dreamina_cli_client_keeps_submit_id_when_task_is_still_querying, test_dreamina_cli_client_downloads_success_result_when_only_url_is_returned (+5) |
| `tests/providers/test_dreamina_cli_video_provider.py` | FakeRunner, test_dreamina_video_client_invokes_text2video_and_returns_output_path, test_dreamina_video_client_raises_querying_with_submit_id, test_dreamina_video_client_invokes_image2video_for_single_image, test_dreamina_video_client_invokes_multimodal2video_for_multiple_images (+2) |
| `tests/providers/test_third_party_image_provider.py` | build_transport, build_timeout_then_success_transport, test_third_party_provider_generates_image_bytes_from_base64_payload, test_third_party_provider_supports_openai_style_image_payload_and_response, test_third_party_provider_normalizes_storyboard_instruction_prompt (+1) |
| `app/providers/image/dreamina_cli_client.py` | DreaminaCliClient, generate_image_file, _build_text2image_command, _resolve_output_path, _find_recent_media_file |
| `app/providers/image/third_party_provider.py` | ThirdPartyImageProvider, generate_image, _normalize_prompt, _extract_structured_fields |
| `tests/providers/test_comfyui_client.py` | build_transport, test_comfyui_client_submits_workflow_and_returns_prompt_id, test_comfyui_client_reads_status_and_downloads_image |
| `tests/providers/test_chatgpt_web_provider.py` | FakeBrowserRunner, test_chatgpt_web_client_passes_profile_dir_and_prompt_suffix, test_chatgpt_web_client_raises_clear_error_when_browser_flow_returns_missing_file |
| `tests/providers/test_codex_cli_provider.py` | __call__, Result, runner |
| `app/providers/image/third_party_client.py` | ThirdPartyImageClient, create_image |
| `app/providers/image/comfyui_client.py` | ComfyUIClient, submit_workflow |

## Entry Points

Start here when exploring this area:

- **`test_dreamina_cli_client_invokes_text2image_and_returns_output_path`** (Function) — `tests/providers/test_dreamina_cli_provider.py:39`
- **`test_dreamina_cli_client_raises_clear_error_when_generation_fails`** (Function) — `tests/providers/test_dreamina_cli_provider.py:129`
- **`test_dreamina_cli_client_keeps_submit_id_when_task_is_still_querying`** (Function) — `tests/providers/test_dreamina_cli_provider.py:148`
- **`test_dreamina_cli_client_downloads_success_result_when_only_url_is_returned`** (Function) — `tests/providers/test_dreamina_cli_provider.py:166`
- **`test_dreamina_cli_client_raises_timeout_with_submit_id_when_available`** (Function) — `tests/providers/test_dreamina_cli_provider.py:212`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `FakeRunner` | Class | `tests/providers/test_dreamina_cli_provider.py` | 8 |
| `DownloadingRunner` | Class | `tests/providers/test_dreamina_cli_provider.py` | 169 |
| `TimeoutRunner` | Class | `tests/providers/test_dreamina_cli_provider.py` | 213 |
| `DreaminaCliClient` | Class | `app/providers/image/dreamina_cli_client.py` | 14 |
| `ThirdPartyImageProvider` | Class | `app/providers/image/third_party_provider.py` | 6 |
| `ThirdPartyImageClient` | Class | `app/providers/image/third_party_client.py` | 3 |
| `FakeRunner` | Class | `tests/providers/test_dreamina_cli_video_provider.py` | 8 |
| `DreaminaCliVideoClient` | Class | `app/providers/video/dreamina_cli_video_client.py` | 5 |
| `ComfyUIClient` | Class | `app/providers/image/comfyui_client.py` | 3 |
| `FakeBrowserRunner` | Class | `tests/providers/test_chatgpt_web_provider.py` | 8 |
| `ChatgptWebClient` | Class | `app/providers/image/chatgpt_web_client.py` | 8 |
| `Result` | Class | `tests/providers/test_codex_cli_provider.py` | 25 |
| `Result` | Class | `tests/providers/test_dreamina_cli_video_provider.py` | 18 |
| `Result` | Class | `tests/providers/test_dreamina_cli_provider.py` | 29 |
| `test_dreamina_cli_client_invokes_text2image_and_returns_output_path` | Function | `tests/providers/test_dreamina_cli_provider.py` | 39 |
| `test_dreamina_cli_client_raises_clear_error_when_generation_fails` | Function | `tests/providers/test_dreamina_cli_provider.py` | 129 |
| `test_dreamina_cli_client_keeps_submit_id_when_task_is_still_querying` | Function | `tests/providers/test_dreamina_cli_provider.py` | 148 |
| `test_dreamina_cli_client_downloads_success_result_when_only_url_is_returned` | Function | `tests/providers/test_dreamina_cli_provider.py` | 166 |
| `test_dreamina_cli_client_raises_timeout_with_submit_id_when_available` | Function | `tests/providers/test_dreamina_cli_provider.py` | 212 |
| `generate_image_file` | Function | `app/providers/image/dreamina_cli_client.py` | 31 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Generate_image_file → _looks_like_media_path` | cross_community | 4 |
| `Refresh_video_job → DreaminaCliClient` | cross_community | 3 |
| `Run_configured_video_job → DreaminaCliVideoClient` | cross_community | 3 |
| `Generate_image_file → _json_candidates` | cross_community | 3 |
| `Generate_image_file → _clean_text_value` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Image | 8 calls |

## How to Explore

1. `gitnexus_context({name: "test_dreamina_cli_client_invokes_text2image_and_returns_output_path"})` — see callers and callees
2. `gitnexus_query({query: "providers"})` — find related execution flows
3. Read key files listed above for implementation details
