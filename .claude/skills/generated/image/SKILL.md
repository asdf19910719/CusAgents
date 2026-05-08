---
name: image
description: "Skill for the Image area of CusAgents. 72 symbols across 18 files."
---

# Image

72 symbols | 18 files | Cohesion: 81%

## When to Use

- Working with code in `app/`
- Understanding how test_build_image_providers_returns_both_registered_backends, test_dreamina_cli_provider_reads_generated_file_bytes, test_chatgpt_web_provider_reads_generated_file_bytes work
- Modifying image-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `app/providers/image/codex_cli_provider.py` | CodexCliClient, generate_image_file, CodexCliImageProvider, generate_image, _build_prompt (+6) |
| `app/providers/image/chatgpt_web_client.py` | __init__, generate_image_file, _run_browser_flow, _resolve_composer, _start_new_chat (+5) |
| `app/providers/image/dreamina_cli_client.py` | DreaminaCliError, query_result, _parse_output, _json_candidates, _merge_json_metadata (+4) |
| `app/providers/video/dreamina_cli_video_client.py` | generate_video_file, _run_command, _build_text2video_command, _build_video_command, _raise_for_video_result (+1) |
| `tests/providers/test_codex_cli_provider.py` | FakeRunner, test_codex_cli_client_invokes_codex_exec_and_returns_output_path, test_codex_cli_provider_reads_generated_file_bytes, test_codex_cli_client_falls_back_to_generated_images_directory, test_codex_cli_client_times_out_with_clear_error (+1) |
| `app/providers/image/dreamina_cli_provider.py` | DreaminaCliImageProvider, generate_image, _build_prompt, _normalize_prompt, _extract_structured_fields |
| `app/providers/image/chatgpt_web_provider.py` | ChatgptWebImageProvider, generate_image, _normalize_prompt, _extract_structured_fields |
| `tests/providers/test_chatgpt_web_provider.py` | test_chatgpt_web_provider_reads_generated_file_bytes, FakeClient, test_chatgpt_web_provider_normalizes_storyboard_instruction_prompt |
| `app/providers/image/comfyui_provider.py` | ComfyUIImageProvider, generate_image, PromptItem |
| `app/providers/image/browser_profile_manager.py` | BrowserProfileManager, ensure_profile_dir, get_download_dir |

## Entry Points

Start here when exploring this area:

- **`test_build_image_providers_returns_both_registered_backends`** (Function) — `tests/services/test_image_factory.py:9`
- **`test_dreamina_cli_provider_reads_generated_file_bytes`** (Function) — `tests/providers/test_dreamina_cli_provider.py:81`
- **`test_chatgpt_web_provider_reads_generated_file_bytes`** (Function) — `tests/providers/test_chatgpt_web_provider.py:18`
- **`test_chatgpt_web_provider_normalizes_storyboard_instruction_prompt`** (Function) — `tests/providers/test_chatgpt_web_provider.py:49`
- **`build_image_providers`** (Function) — `app/services/factory.py:27`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `FakeClient` | Class | `tests/providers/test_dreamina_cli_provider.py` | 85 |
| `FakeClient` | Class | `tests/providers/test_chatgpt_web_provider.py` | 22 |
| `WorkflowBuilder` | Class | `app/providers/image/workflow_builder.py` | 0 |
| `DreaminaCliImageProvider` | Class | `app/providers/image/dreamina_cli_provider.py` | 5 |
| `ComfyUIImageProvider` | Class | `app/providers/image/comfyui_provider.py` | 3 |
| `ChatgptWebImageProvider` | Class | `app/providers/image/chatgpt_web_provider.py` | 5 |
| `BrowserProfileManager` | Class | `app/providers/image/browser_profile_manager.py` | 3 |
| `BaseImageProvider` | Class | `app/providers/image/base.py` | 15 |
| `DreaminaCliError` | Class | `app/providers/image/dreamina_cli_client.py` | 6 |
| `FakeRunner` | Class | `tests/providers/test_codex_cli_provider.py` | 6 |
| `CodexCliClient` | Class | `app/providers/image/codex_cli_provider.py` | 10 |
| `CodexCliImageProvider` | Class | `app/providers/image/codex_cli_provider.py` | 170 |
| `ImageGenerationResult` | Class | `app/providers/image/base.py` | 6 |
| `PromptItem` | Class | `app/providers/image/comfyui_provider.py` | 10 |
| `test_build_image_providers_returns_both_registered_backends` | Function | `tests/services/test_image_factory.py` | 9 |
| `test_dreamina_cli_provider_reads_generated_file_bytes` | Function | `tests/providers/test_dreamina_cli_provider.py` | 81 |
| `test_chatgpt_web_provider_reads_generated_file_bytes` | Function | `tests/providers/test_chatgpt_web_provider.py` | 18 |
| `test_chatgpt_web_provider_normalizes_storyboard_instruction_prompt` | Function | `tests/providers/test_chatgpt_web_provider.py` | 49 |
| `build_image_providers` | Function | `app/services/factory.py` | 27 |
| `generate_image` | Function | `app/providers/image/chatgpt_web_provider.py` | 10 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Generate_video_file → _looks_like_media_path` | intra_community | 5 |
| `Generate_image → _is_image_file` | cross_community | 5 |
| `Query_submit_id → _looks_like_media_path` | cross_community | 5 |
| `Generate_video_file → _json_candidates` | intra_community | 4 |
| `Generate_video_file → _clean_text_value` | intra_community | 4 |
| `Generate_image_file → _looks_like_media_path` | cross_community | 4 |
| `Generate_image → _extract_structured_fields` | intra_community | 4 |
| `Generate_image → _extract_structured_fields` | intra_community | 4 |
| `Query_submit_id → _json_candidates` | cross_community | 4 |
| `Query_submit_id → _clean_text_value` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Providers | 6 calls |
| Commands | 1 calls |
| Routes | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_build_image_providers_returns_both_registered_backends"})` — see callers and callees
2. `gitnexus_query({query: "image"})` — find related execution flows
3. Read key files listed above for implementation details
