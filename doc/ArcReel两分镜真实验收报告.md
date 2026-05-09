# ArcReel 两分镜真实验收报告

## Environment

- Date: 2026-05-08 / 2026-05-09
- ArcReel local-source URL: `http://127.0.0.1:1242`
- ArcReel baseline URL: `http://127.0.0.1:1241` (stopped during Dreamina validation to avoid old worker claiming shared DB tasks)
- Container: `arcreel-local-cusagents`
- Container image: `ghcr.io/arcreel/arcreel:latest`
- Health: `GET /health` returned HTTP 200.
- Auth: `POST /api/v1/auth/token` with local `.env` credentials returned a bearer token.

## Project

- Title: `雨夜追踪`
- Project name: `arcreel-two-shot-acceptance`
- Story:
  - 分镜 1：侦探在霓虹雨巷发现带血怀表。
  - 分镜 2：黑衣人回头，怀表倒映出失踪女孩的脸。
- API result: `POST /api/v1/projects` succeeded.
- Project file: `runtime/research/ArcReel/deploy/projects/arcreel-two-shot-acceptance/project.json`

## References

- Character reference: placeholder local PNGs were created for `detective`, `man_in_black`, and `missing_girl`.
- Scene reference: placeholder local PNG was created for `neon_alley`.
- Prop reference: placeholder local PNG was created for `bloody_watch`.
- Storyboard references: placeholder local PNGs were created for `S1` and `S2`.
- Reason: placeholders were used to validate ArcReel-to-CusAgents reference-image plumbing without consuming Dreamina/ChatGPT Web quota.

## Shot 1 Video Task

- Submitted through local-source ArcReel at `http://127.0.0.1:1242`.
- Successful task id: `c9500d4c24b94d4bb628e00225b0b92a`.
- ArcReel task status: `succeeded`.
- CusAgents bridge job id: `296`.
- CusAgents bridge status: `completed`.
- Dreamina submit_id: `c40c88fe-ab15-4eef-bea5-f1f358cb72af`.
- Dreamina result: `gen_status=success`, `credit_count=12`.
- Downloaded CusAgents file: `output/dreamina/videos/c40c88fe-ab15-4eef-bea5-f1f358cb72af_video_1.mp4`.
- Mirrored ArcReel project file: `runtime/research/ArcReel/deploy/projects/arcreel-two-shot-acceptance/videos/scene_S1.mp4`.
- Script backfill: `segments[0].generated_assets.video_clip = "videos/scene_S1.mp4"`.
- Mode: `multimodal2video`.
- Reference prompt includes: `scene_S1.png`, `detective.png`, `neon_alley.png`, `bloody_watch.png`.
- Reference manifest persisted in CusAgents video job `296` with 4 images and no dropped images.
- Note: S1 initially completed before ArcReel resume had script backfill logic; this was fixed by making resume update `generated_assets.video_clip` and by adding compensation for already `succeeded` tasks.

## Shot 2 Video Task

- Submitted through local-source ArcReel at `http://127.0.0.1:1242`.
- Task id: `08561e741e4741b5992ad29ccedcc9c7`.
- CusAgents bridge job id: `338`.
- Dreamina submit_id: `311b33ed-32a5-4f49-be27-aca0681949d9`.
- Current status: `gen_status=querying`.
- Background polling: enabled through `arcreel-acceptance` RQ scheduled jobs.
- Last verified scheduled poll: UUID `1783875d-4924-4085-9341-51cde39cf1f8`, tracked by Redis key `video-poll:arcreel-acceptance:338`.
- Script backfill: pending.
- Note: do not resubmit S2; continue polling the existing submit_id.

## Notifications

- Not verified.

## Result

- Partial acceptance pending S2 completion.
- Confirmed:
  - ArcReel container is healthy.
  - Local credentials work.
  - Project creation through ArcReel API works.
  - CusAgents command layer now supports optional `ARCREEL_API_TOKEN` for authenticated ArcReel calls.
  - A local-source ArcReel container on `http://127.0.0.1:1242` exposes `POST /api/v1/projects/{name}/resume`.
  - CusAgents `/arcreel_resume` command routing can call the local-source ArcReel instance with a bearer token.
  - CusAgents provider config in ArcReel can construct `cusagents` and `cusagents-dreamina-video` backends with `api_key` ignored and `base_url` honored.
  - `S1` video task reached Dreamina success, downloaded an mp4, mirrored the file into the ArcReel project, and backfilled `episode_1.json`.
  - `S2` video task was submitted once and remains queryable through bridge job `338`.
  - CusAgents now uses API + RQ worker + explicit scheduler for video polling; scheduled poll jobs use generated UUIDs plus a short Redis dedupe key instead of a fixed job id.
- Not confirmed:
  - Real AI reference generation.
  - S2 refresh-to-completion.
  - Final two-shot complete script state.

## Open Issues

- The original `1241` Docker service uses the published image `ghcr.io/arcreel/arcreel:latest` and does not mount the local modified `server/` source. A separate local-source container on `1242` was used to verify the new resume endpoint.
- `deploy-arcreel-1` and `arcreel-local-cusagents` share the same `deploy/projects` mount and therefore the same ArcReel task DB. The baseline container was stopped during Task 10 validation because its worker could claim CusAgents tasks and fail with `Unknown provider: cusagents`.
- The ArcReel pytest suite is blocked in this local Python environment by SQLAlchemy async engine configuration loading synchronous `pysqlite`; use the project-managed environment or Docker test environment before claiming ArcReel tests pass.
- On this Windows validation host, `rq.SimpleWorker --with-scheduler` did not move due scheduled jobs by itself; `python scripts/run_scheduler.py` is required alongside the worker for delayed video polling.
- A real two-shot completion still requires S2 submit_id `311b33ed-32a5-4f49-be27-aca0681949d9` to return success, then bridge refresh and ArcReel resume.
