# ArcReel 本地运行验收记录

## 许可结论

- ArcReel license: AGPL-3.0。
- 当前用途：本机内部验证与改造评估。
- 第一阶段不分发改造版本，不把 ArcReel 源码复制进 CusAgents 主仓库。
- 若未来对外分发或商业闭源使用，需要重新评估 AGPL-3.0 义务。

## 运行环境

- Host: Windows + Docker Desktop + WSL2。
- ArcReel source: `runtime/research/ArcReel`。
- CusAgents source: `E:\AIProject\CusAgents`。
- Docker: `Docker version 29.2.1, build a5c7197`。
- WSL2: `docker-desktop` running。

## ArcReel Docker 基线

- Start command: `docker compose -f runtime\research\ArcReel\deploy\docker-compose.yml up -d`
- Health URL: `http://127.0.0.1:1241/health`
- Login URL: `http://127.0.0.1:1241`
- Local username: `admin`
- Local password source: `runtime/research/ArcReel/deploy/.env`
- Image: `ghcr.io/arcreel/arcreel:latest`
- Image digest: `sha256:1575c60488722f4616185edbf74fa9be3e3b673881fa2668c839eb121ce6f439`
- Container: `deploy-arcreel-1`
- Result: passed
- Notes:
  - `127.0.0.1:1241` 在启动前未连通。
  - 首次 `docker compose up -d` 拉取镜像超时，改为先执行 `docker pull ghcr.io/arcreel/arcreel:latest` 后再次启动成功。
  - `GET http://127.0.0.1:1241/health` 返回 `200`，响应为 `{"status":"ok","message":"视频项目管理 WebUI 运行正常"}`。
  - 容器日志确认数据库 schema 已是最新、`GenerationWorker` 已启动、`ProjectEventService` 已启动、`Uvicorn` 监听 `0.0.0.0:1241`。
  - 本地登录地址为 `http://127.0.0.1:1241`；本轮只验证 health 与服务启动，未执行浏览器登录验收。

## 2026-05-08 API 前置验收

- `POST /api/v1/auth/token` 使用 `admin` / `arcreel-local-dev` 登录成功，返回 bearer token。
- `POST /api/v1/projects` 创建 `arcreel-two-shot-acceptance` 成功，项目文件写入 `runtime/research/ArcReel/deploy/projects/arcreel-two-shot-acceptance/project.json`。
- `POST /api/v1/projects/arcreel-two-shot-acceptance/resume` 在当前运行容器返回 HTTP 405；当前容器使用 `ghcr.io/arcreel/arcreel:latest`，只挂载 `.env`、`projects`、`vertex_keys`、`claude_data`，未挂载本地改造后的 `server/` 源码，因此不包含本轮新增 resume endpoint。
- 本轮未触发真实图片/视频生成，未消耗 Dreamina、ChatGPT Web 或大模型额度。

## 2026-05-08 本地改造源码容器

- 本地镜像构建命令：`docker build -t arcreel-local:cusagents-bridge .`
- 构建结果：失败，阻断于 Docker Hub 拉取 `node:22-slim` 元数据超时。
- 替代运行方式：基于已存在的 `ghcr.io/arcreel/arcreel:latest` 启动 `arcreel-local-cusagents`，映射 `1242:1241`，并 bind mount 本地改造后的 `lib/`、`server/`、`alembic/`、`alembic.ini` 覆盖容器内 `/app` 对应路径。
- 容器启动结果：`arcreel-local-cusagents` healthy。
- 启动日志确认执行本地迁移：`Running upgrade 4c643f3ff5b9 -> 8f4a0c9b2d71, include querying in active task dedupe`。
- `GET http://127.0.0.1:1242/health` 返回 HTTP 200。
- `POST http://127.0.0.1:1242/api/v1/projects/arcreel-two-shot-acceptance/resume` 返回 HTTP 200，响应为 `{"success":true,"project_name":"arcreel-two-shot-acceptance","resume":{"processed":0,"skipped":0,"updated":0}}`。
- CusAgents 命令路由以 `ARCREEL_BASE_URL=http://127.0.0.1:1242` 和 `ARCREEL_API_TOKEN=<login token>` 调用 `/arcreel_resume project="arcreel-two-shot-acceptance"` 成功，返回 `resume_requested`。
- 容器内 `uv run python -m py_compile lib/cusagents_bridge/video_resume.py server/routers/projects.py` 通过。
- 容器内 pytest 未执行成功，原因是该临时容器未挂载 `tests/`，`uv run pytest tests/test_arcreel_project_resume_router.py tests/test_cusagents_video_resume.py -q` 返回 `file or directory not found`。

## 2026-05-08 Task 10 S1 bridge validation

- Active local-source ArcReel: `arcreel-local-cusagents` on `http://127.0.0.1:1242`.
- Current CusAgents bridge API: `http://127.0.0.1:8010`, verified by `GET /arcreel/bridge/health`.
- Baseline ArcReel container `deploy-arcreel-1` was stopped for this validation because it shares `/app/projects` with the local-source container and can otherwise claim tasks from the same DB with the unmodified published-image worker.
- ArcReel provider credentials were created for `cusagents` and `cusagents-dreamina-video`, both with `base_url=http://host.docker.internal:8010/`.
- Project `arcreel-two-shot-acceptance` now contains local placeholder references and `scripts/episode_1.json`; these placeholders are local validation assets and are not AI-generated outputs.
- Submitted `S1` through `POST /api/v1/projects/arcreel-two-shot-acceptance/generate/video/S1`.
- Successful ArcReel task id: `c9500d4c24b94d4bb628e00225b0b92a`.
- ArcReel task status after worker processing: `querying`.
- CusAgents bridge job id: `296`; status `pending`; mode `multimodal2video`; model `seedance2.0`.
- CusAgents prompt contains reference file names: `scene_S1.png`, `detective.png`, `neon_alley.png`, `bloody_watch.png`.
- Project resume result after bridge pending refresh: `processed=1`, `skipped=0`, `updated=1`.
