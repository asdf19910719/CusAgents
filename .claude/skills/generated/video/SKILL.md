---
name: video
description: "Skill for the Video area of CusAgents. 15 symbols across 7 files."
---

# Video

15 symbols | 7 files | Cohesion: 82%

## When to Use

- Working with code in `app/`
- Understanding how generate_video, test_dreamina_video_provider_reads_generated_file_bytes, test_dreamina_video_provider_defaults_to_seedance2 work
- Modifying video-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/providers/test_dreamina_cli_video_provider.py` | test_dreamina_video_provider_reads_generated_file_bytes, FakeClient, test_dreamina_video_provider_defaults_to_seedance2, test_dreamina_video_provider_routes_structured_request |
| `app/providers/video/base.py` | VideoGenerationResult, VideoGenerationRequest, image_paths, BaseVideoProvider |
| `app/workers/video_jobs.py` | execute_video_job, run_configured_video_job |
| `app/providers/video/dreamina_cli_video_provider.py` | DreaminaCliVideoProvider, generate_video |
| `tests/services/test_video_service.py` | generate_video |
| `app/services/video_service.py` | _build_generation_input |
| `app/services/factory.py` | build_video_service |

## Entry Points

Start here when exploring this area:

- **`generate_video`** (Function) — `tests/services/test_video_service.py:15`
- **`test_dreamina_video_provider_reads_generated_file_bytes`** (Function) — `tests/providers/test_dreamina_cli_video_provider.py:67`
- **`test_dreamina_video_provider_defaults_to_seedance2`** (Function) — `tests/providers/test_dreamina_cli_video_provider.py:119`
- **`test_dreamina_video_provider_routes_structured_request`** (Function) — `tests/providers/test_dreamina_cli_video_provider.py:231`
- **`execute_video_job`** (Function) — `app/workers/video_jobs.py:6`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `FakeClient` | Class | `tests/providers/test_dreamina_cli_video_provider.py` | 71 |
| `DreaminaCliVideoProvider` | Class | `app/providers/video/dreamina_cli_video_provider.py` | 3 |
| `VideoGenerationResult` | Class | `app/providers/video/base.py` | 6 |
| `VideoGenerationRequest` | Class | `app/providers/video/base.py` | 19 |
| `BaseVideoProvider` | Class | `app/providers/video/base.py` | 45 |
| `generate_video` | Function | `tests/services/test_video_service.py` | 15 |
| `test_dreamina_video_provider_reads_generated_file_bytes` | Function | `tests/providers/test_dreamina_cli_video_provider.py` | 67 |
| `test_dreamina_video_provider_defaults_to_seedance2` | Function | `tests/providers/test_dreamina_cli_video_provider.py` | 119 |
| `test_dreamina_video_provider_routes_structured_request` | Function | `tests/providers/test_dreamina_cli_video_provider.py` | 231 |
| `execute_video_job` | Function | `app/workers/video_jobs.py` | 6 |
| `run_configured_video_job` | Function | `app/workers/video_jobs.py` | 16 |
| `build_video_service` | Function | `app/services/factory.py` | 142 |
| `generate_video` | Function | `app/providers/video/dreamina_cli_video_provider.py` | 20 |
| `image_paths` | Function | `app/providers/video/base.py` | 32 |
| `_build_generation_input` | Function | `app/services/video_service.py` | 84 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Run_configured_video_job → VideoGenerationRequest` | cross_community | 5 |
| `Run_configured_video_job → FeishuAppMessageNotifier` | cross_community | 4 |
| `Run_configured_video_job → FeishuWebhookNotifier` | cross_community | 4 |
| `Run_configured_video_job → NotificationService` | cross_community | 4 |
| `Run_configured_video_job → VideoAsset` | cross_community | 4 |
| `Run_configured_video_job → _notify` | cross_community | 4 |
| `Run_configured_video_job → Build_video_completion_message` | cross_community | 4 |
| `Run_configured_video_job → Settings` | cross_community | 3 |
| `Run_configured_video_job → DreaminaCliVideoProvider` | intra_community | 3 |
| `Run_configured_video_job → DreaminaCliVideoClient` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Services | 2 calls |
| Scripts | 2 calls |
| Image | 1 calls |
| Routes | 1 calls |
| Providers | 1 calls |

## How to Explore

1. `gitnexus_context({name: "generate_video"})` — see callers and callees
2. `gitnexus_query({query: "video"})` — find related execution flows
3. Read key files listed above for implementation details
