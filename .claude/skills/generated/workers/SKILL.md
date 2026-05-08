---
name: workers
description: "Skill for the Workers area of CusAgents. 19 symbols across 10 files."
---

# Workers

19 symbols | 10 files | Cohesion: 81%

## When to Use

- Working with code in `app/`
- Understanding how test_build_job_dispatcher_defaults_to_noop_when_auto_enqueue_disabled, test_build_job_dispatcher_uses_rq_when_auto_enqueue_enabled, build_job_dispatcher work
- Modifying workers-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `app/workers/dispatcher.py` | JobDispatcher, NoopJobDispatcher, RQJobDispatcher, build_job_dispatcher, enqueue_job (+2) |
| `tests/services/test_dispatcher_service.py` | test_build_job_dispatcher_defaults_to_noop_when_auto_enqueue_disabled, test_build_job_dispatcher_uses_rq_when_auto_enqueue_enabled |
| `tests/workers/test_runner.py` | test_build_worker_uses_simple_worker_on_windows, FakeQueue |
| `app/workers/runner.py` | build_worker, run_worker |
| `app/api/routes/videos.py` | get_video_dispatcher |
| `app/api/routes/story_videos.py` | get_story_video_dispatcher |
| `app/api/routes/jobs.py` | get_job_dispatcher |
| `scripts/run_worker.py` | main |
| `app/core/logging.py` | setup_logging |
| `app/workers/queue.py` | create_queue |

## Entry Points

Start here when exploring this area:

- **`test_build_job_dispatcher_defaults_to_noop_when_auto_enqueue_disabled`** (Function) — `tests/services/test_dispatcher_service.py:4`
- **`test_build_job_dispatcher_uses_rq_when_auto_enqueue_enabled`** (Function) — `tests/services/test_dispatcher_service.py:15`
- **`build_job_dispatcher`** (Function) — `app/workers/dispatcher.py:47`
- **`get_video_dispatcher`** (Function) — `app/api/routes/videos.py:22`
- **`get_story_video_dispatcher`** (Function) — `app/api/routes/story_videos.py:15`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `JobDispatcher` | Class | `app/workers/dispatcher.py` | 4 |
| `NoopJobDispatcher` | Class | `app/workers/dispatcher.py` | 15 |
| `RQJobDispatcher` | Class | `app/workers/dispatcher.py` | 26 |
| `FakeQueue` | Class | `tests/workers/test_runner.py` | 4 |
| `test_build_job_dispatcher_defaults_to_noop_when_auto_enqueue_disabled` | Function | `tests/services/test_dispatcher_service.py` | 4 |
| `test_build_job_dispatcher_uses_rq_when_auto_enqueue_enabled` | Function | `tests/services/test_dispatcher_service.py` | 15 |
| `build_job_dispatcher` | Function | `app/workers/dispatcher.py` | 47 |
| `get_video_dispatcher` | Function | `app/api/routes/videos.py` | 22 |
| `get_story_video_dispatcher` | Function | `app/api/routes/story_videos.py` | 15 |
| `get_job_dispatcher` | Function | `app/api/routes/jobs.py` | 20 |
| `main` | Function | `scripts/run_worker.py` | 10 |
| `test_build_worker_uses_simple_worker_on_windows` | Function | `tests/workers/test_runner.py` | 3 |
| `build_worker` | Function | `app/workers/runner.py` | 9 |
| `run_worker` | Function | `app/workers/runner.py` | 15 |
| `setup_logging` | Function | `app/core/logging.py` | 3 |
| `create_queue` | Function | `app/workers/queue.py` | 4 |
| `enqueue_job` | Function | `app/workers/dispatcher.py` | 5 |
| `enqueue_codex_run` | Function | `app/workers/dispatcher.py` | 8 |
| `enqueue_video_job` | Function | `app/workers/dispatcher.py` | 11 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Handle_message_receive_v1 → Settings` | cross_community | 5 |
| `Get_video_dispatcher → Settings` | cross_community | 4 |
| `Get_story_video_dispatcher → Settings` | cross_community | 4 |
| `Get_job_dispatcher → Settings` | cross_community | 4 |
| `Handle_message_receive_v1 → RQJobDispatcher` | cross_community | 4 |
| `Handle_message_receive_v1 → NoopJobDispatcher` | cross_community | 4 |
| `Main → Settings` | cross_community | 4 |
| `Get_video_dispatcher → RQJobDispatcher` | intra_community | 3 |
| `Get_video_dispatcher → NoopJobDispatcher` | intra_community | 3 |
| `Get_story_video_dispatcher → RQJobDispatcher` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Commands | 2 calls |
| Scripts | 2 calls |

## How to Explore

1. `gitnexus_context({name: "test_build_job_dispatcher_defaults_to_noop_when_auto_enqueue_disabled"})` — see callers and callees
2. `gitnexus_query({query: "workers"})` — find related execution flows
3. Read key files listed above for implementation details
