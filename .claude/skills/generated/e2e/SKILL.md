---
name: e2e
description: "Skill for the E2e area of CusAgents. 10 symbols across 3 files."
---

# E2e

10 symbols | 3 files | Cohesion: 81%

## When to Use

- Working with code in `tests/`
- Understanding how test_execute_job_processes_job_with_session_factory, test_run_configured_job_uses_built_orchestration_service, test_run_configured_job_loads_runtime_settings work
- Modifying e2e-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/e2e/test_worker_flow.py` | FakeOrchestrationService, test_execute_job_processes_job_with_session_factory, test_run_configured_job_uses_built_orchestration_service, test_run_configured_job_loads_runtime_settings, fake_build_orchestration_service |
| `app/workers/jobs.py` | execute_job, run_default_job, run_configured_job |
| `tests/e2e/test_codex_conversation_flow.py` | fake_runner, Result |

## Entry Points

Start here when exploring this area:

- **`test_execute_job_processes_job_with_session_factory`** (Function) — `tests/e2e/test_worker_flow.py:20`
- **`test_run_configured_job_uses_built_orchestration_service`** (Function) — `tests/e2e/test_worker_flow.py:51`
- **`test_run_configured_job_loads_runtime_settings`** (Function) — `tests/e2e/test_worker_flow.py:88`
- **`fake_build_orchestration_service`** (Function) — `tests/e2e/test_worker_flow.py:102`
- **`execute_job`** (Function) — `app/workers/jobs.py:9`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `FakeOrchestrationService` | Class | `tests/e2e/test_worker_flow.py` | 11 |
| `Result` | Class | `tests/e2e/test_codex_conversation_flow.py` | 23 |
| `test_execute_job_processes_job_with_session_factory` | Function | `tests/e2e/test_worker_flow.py` | 20 |
| `test_run_configured_job_uses_built_orchestration_service` | Function | `tests/e2e/test_worker_flow.py` | 51 |
| `test_run_configured_job_loads_runtime_settings` | Function | `tests/e2e/test_worker_flow.py` | 88 |
| `fake_build_orchestration_service` | Function | `tests/e2e/test_worker_flow.py` | 102 |
| `execute_job` | Function | `app/workers/jobs.py` | 9 |
| `run_default_job` | Function | `app/workers/jobs.py` | 19 |
| `run_configured_job` | Function | `app/workers/jobs.py` | 28 |
| `fake_runner` | Function | `tests/e2e/test_codex_conversation_flow.py` | 19 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Run_configured_job → OpenAICompatibleProvider` | cross_community | 4 |
| `Run_default_job → Get` | cross_community | 3 |
| `Run_configured_job → Settings` | cross_community | 3 |
| `Run_configured_job → PromptTemplateService` | cross_community | 3 |
| `Run_configured_job → CacheService` | cross_community | 3 |
| `Run_configured_job → OutlineService` | cross_community | 3 |
| `Run_configured_job → Get` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Services | 3 calls |
| Routes | 1 calls |
| Scripts | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_execute_job_processes_job_with_session_factory"})` — see callers and callees
2. `gitnexus_query({query: "e2e"})` — find related execution flows
3. Read key files listed above for implementation details
