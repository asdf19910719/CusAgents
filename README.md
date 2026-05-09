# Custom Agents

一个面向内容生成流水线的最小可运行服务骨架，当前已经支持四类出图后端：

1. `comfyui_remote`
   当前项目通过 HTTP API 调用另一台机器或本机上的 ComfyUI
2. `third_party`
   当前项目通过第三方图像 API 出图
3. `codex_cli`
   当前项目通过本机已登录的 Codex CLI 做实验型出图
4. `chatgpt_web`
   当前项目通过 Playwright 复用独立网页登录态，在 ChatGPT 网页中模拟人工操作出图

文本链路保持统一：

1. `Job` 创建与状态查询
2. 故事大纲生成
3. 分镜结构化生成
4. Prompt 组装
5. 按任务选择出图后端
6. 质量检查、人工审核入口与成本统计
7. 飞书通知出口与通知日志
8. 飞书命令入口与命令审计

## 当前技术栈

1. `FastAPI`
2. `SQLAlchemy + Alembic`
3. `Pydantic v2`
4. `Redis + RQ`
5. `httpx`
6. `Jinja2`
7. `lark-oapi`
8. `pytest`

## 环境变量

参考 [.env.example](E:/AIProject/CusAgents/.env.example)：

1. `APP_ENV`
2. `DATABASE_URL`
3. `REDIS_URL`
4. `LLM_BASE_URL`
5. `LLM_API_KEY`
6. `LLM_DEFAULT_MODEL`
7. `COMFYUI_BASE_URL`
8. `OUTPUT_DIR`
9. `IMAGE_BACKEND`
10. `THIRD_PARTY_IMAGE_BASE_URL`
11. `THIRD_PARTY_IMAGE_API_KEY`
12. `THIRD_PARTY_IMAGE_MODEL`
13. `THIRD_PARTY_IMAGE_API_PATH`
14. `FEISHU_NOTIFY_WEBHOOK_URL`
15. `FEISHU_VERIFICATION_TOKEN`
16. `FEISHU_ENCRYPT_KEY`
17. `FEISHU_APP_ID`
18. `FEISHU_APP_SECRET`
19. `FEISHU_OPEN_BASE_URL`
20. `FEISHU_WEBHOOK_MAX_AGE_SECONDS`
21. `MOBILE_ACCESS_TOKEN`
22. `MOBILE_SESSION_MAX_AGE_SECONDS`
23. `CODEX_CLI_COMMAND`
24. `CODEX_CLI_MODEL`
25. `CHATGPT_WEB_BASE_URL`
26. `CHATGPT_WEB_PROFILE_DIR`
27. `CHATGPT_WEB_HEADLESS`
28. `CHATGPT_WEB_TIMEOUT_SECONDS`
29. `CHATGPT_WEB_BROWSER_CHANNEL`
30. `CHATGPT_WEB_EXECUTABLE_PATH`
31. `CHATGPT_WEB_CDP_URL`
32. `CHATGPT_WEB_IMAGE_PROMPT_SUFFIX`
33. `AUTO_ENQUEUE_JOBS`
34. `QUEUE_NAME`
35. `CONVERSATION_IDLE_TIMEOUT_SECONDS`
36. `CONVERSATION_COMPACT_TRIGGER_COUNT`
37. `CONVERSATION_KEEP_RECENT_COUNT`

说明：

1. `IMAGE_BACKEND` 是系统默认出图后端
2. 每个 `Job` 也可以单独指定 `image_backend`
3. 当前支持值：
   `comfyui_remote`
   `third_party`
   `codex_cli`
   `chatgpt_web`
4. `FEISHU_NOTIFY_WEBHOOK_URL` 配置后，系统会在任务创建、等待审核、失败等事件写通知日志，并尝试推送飞书 webhook
5. `FEISHU_VERIFICATION_TOKEN` 用于飞书事件入口的最小 token 校验
6. `FEISHU_ENCRYPT_KEY` 用于飞书事件入口签名校验；配置后会同时启用时间窗校验和 Redis 优先、内存兜底的重放保护
7. `FEISHU_APP_ID`、`FEISHU_APP_SECRET` 与 `FEISHU_OPEN_BASE_URL` 用于飞书应用消息回发与长连接客户端
8. `MOBILE_ACCESS_TOKEN` 配置后，手机轻控制页会要求先登录，再通过短期 session cookie 访问
9. `CODEX_CLI_COMMAND` 与 `CODEX_CLI_MODEL` 用于实验型 `codex_cli` 出图后端
10. `CHATGPT_WEB_*` 用于浏览器自动化出图后端；首次使用前需要先执行登录脚本，写入独立 Playwright profile
11. `CONVERSATION_IDLE_TIMEOUT_SECONDS` 用于控制同一个飞书 `chat_id` 的 Codex 会话空闲多久后自动切新会话
12. `CONVERSATION_COMPACT_TRIGGER_COUNT` 与 `CONVERSATION_KEEP_RECENT_COUNT` 用于控制会话摘要压缩

## 本地安装

```bash
python -m pip install -r requirements.txt
```

## 启动 API

```bash
uvicorn app.main:app --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

运行期诊断：

```bash
curl http://127.0.0.1:8000/admin/runtime/health
```

这个接口会返回数据库、Redis、LLM 配置、`comfyui_remote`、`third_party`、`codex_cli` 的当前状态，适合联调前快速判断是配置缺失、服务不可达，还是队列未开启。

## 初始化 ChatGPT Web 登录态

如果要使用 `chatgpt_web`，推荐使用普通 Chrome + CDP 模式。先准备独立浏览器 profile：

```bash
python scripts/run_chatgpt_web_browser.py --check
python scripts/run_chatgpt_web_browser.py
```

说明：

1. 该脚本会打开普通 Chrome，并通过 `CHATGPT_WEB_CDP_URL` 暴露给 Playwright 复用
2. 会话目录默认是 `CHATGPT_WEB_PROFILE_DIR`
3. 请在打开的页面里完成 ChatGPT 登录
4. 建议不要复用你日常浏览器 profile，当前实现默认使用独立 profile
5. `CHATGPT_WEB_EXECUTABLE_PATH` 推荐指向真实 Chrome，例如 `C:\Program Files\Google\Chrome\Application\chrome.exe`
6. 如果不使用 CDP 模式，也可以用 `python scripts/run_chatgpt_web_login.py` 打开 Playwright 持久化浏览器，但它更容易触发 ChatGPT 登录挑战

## 启动 Worker

当前 Worker 依赖本地可用的 Redis：

```bash
python scripts/run_worker.py
python scripts/run_worker.py --check
```

`--check` 只验证脚本入口与依赖导入，不启动真实队列消费。

如果使用视频这类长任务的后台轮询，还需要单独启动 scheduler，把 RQ 延迟任务按计划搬回队列：

```bash
python scripts/run_scheduler.py
python scripts/run_scheduler.py --check
```

运行时建议同时保持 `API`、`worker`、`scheduler` 三个进程在线。`worker` 负责执行队列任务，`scheduler` 只负责定时投递到期任务。

## 启动飞书长连接客户端

如果不走公网 webhook，可以直接使用官方 SDK 长连接模式：

```bash
python scripts/run_feishu_long_connection.py
python scripts/run_feishu_long_connection.py --check
python scripts/run_feishu_long_connection.py --connect-check
```

说明：

1. 这条链路复用现有命令层，不替换 `POST /webhooks/feishu/events`
2. 需要已配置 `FEISHU_APP_ID` 与 `FEISHU_APP_SECRET`
3. 适合“飞书发命令 -> 本地执行 -> 飞书收结果”的单机控制场景
4. 如果飞书后台切换到长连接模式，就不再依赖公网回调 URL
5. `--check` 只验证配置和客户端构造
6. `--connect-check` 会真实建立并断开一次飞书长连接，用于联调确认建联能力

如果要让 `POST /jobs` 创建任务后自动入队，需要启用：

```text
AUTO_ENQUEUE_JOBS=true
QUEUE_NAME=custom-agents
```

## 提交一个测试任务

直接调用 API：

```bash
curl -X POST http://127.0.0.1:8000/jobs ^
  -H "Content-Type: application/json" ^
  -d "{\"topic\":\"冷血剑客复仇\",\"style_preset\":\"cinematic\",\"target_shot_count\":3,\"image_backend\":\"comfyui_remote\"}"
```

如果要切到第三方 API：

```bash
curl -X POST http://127.0.0.1:8000/jobs ^
  -H "Content-Type: application/json" ^
  -d "{\"topic\":\"冷血剑客复仇\",\"style_preset\":\"cinematic\",\"target_shot_count\":3,\"image_backend\":\"third_party\"}"
```

或者使用演示脚本：

```bash
python scripts/demo_request.py --base-url http://127.0.0.1:8000 --image-backend comfyui_remote
python scripts/demo_request.py --base-url http://127.0.0.1:8000 --image-backend third_party
python scripts/demo_request.py --base-url http://127.0.0.1:8000 --image-backend codex_cli
python scripts/demo_request.py --base-url http://127.0.0.1:8000 --image-backend chatgpt_web
python scripts/demo_request.py --base-url http://127.0.0.1:8000 --image-backend dreamina_cli
```

## Dreamina / 即梦 CLI

当前新增两个即梦链路：

1. `dreamina_cli`：图片后端，可用于 `POST /jobs`、移动端创建任务和飞书 `/create ... backend=dreamina_cli`。
2. `dreamina_video_cli`：独立视频后端，可用于 `POST /videos` 和飞书 `/video prompt="..." duration=4 ratio=16:9 model=seedance2.0`。项目默认视频模型是 `seedance2.0`。

即梦任务会消耗账号额度，默认不自动重试。运行前建议检查：

```bash
C:\Users\91799\bin\dreamina.exe user_credit
C:\Users\91799\bin\dreamina.exe text2image --help
C:\Users\91799\bin\dreamina.exe text2video --help
```

视频任务通常需要几十分钟甚至更久。`querying` 是可恢复长任务状态，不按短任务失败处理；系统会保留 `submit_id`，后续可查询与恢复：

```bash
curl -X POST http://127.0.0.1:8000/videos/{video_id}/refresh
C:\Users\91799\bin\dreamina.exe query_result --submit_id=<submit_id> --download_dir=./output/dreamina/videos
```

开启 `AUTO_ENQUEUE_JOBS=true` 后，视频提交和手动 refresh 会在仍为 `querying` 时安排后台 poll。后台 poll 依赖 `python scripts/run_scheduler.py` 和 `python scripts/run_worker.py` 同时运行。

当前 `POST /jobs` 返回中会包含：

1. `dispatch_status`
2. `queue_name`
3. `dispatch_error`

`image_backend` 只接受：

1. `comfyui_remote`
2. `third_party`
3. `codex_cli`
4. `chatgpt_web`

如果传入其它值，API 会直接返回 `422`，避免任务入库后才在 Worker 阶段失败。

## 飞书通知出口

当前已支持最小飞书通知出口：

1. `POST /jobs` 创建任务后会写一条 `job_created` 通知记录
2. Worker 执行结束进入 `waiting_review` 时会写 `job_waiting_review`
3. Worker 执行失败时会写 `job_failed`

如果配置：

```text
FEISHU_NOTIFY_WEBHOOK_URL=https://open.feishu.cn/...
```

系统会在写通知日志的同时尝试发送飞书 webhook 消息；未配置时，通知会被记录为 `skipped`，不会影响主任务流程。

## 飞书命令入口

当前已支持最小飞书事件入口：

```text
POST /webhooks/feishu/events
```

当前支持：

1. `url_verification` challenge 校验
2. 文本命令解析
3. 命令执行审计
4. 命令结果通知记录

第一版支持的命令：

```text
/create topic="赛博 武侠" style=cinematic shots=2 backend=third_party
/status job=123
/retry job=123
/approve job=123
/cancel job=123
/assets job=123
/health
```

说明：

1. 当前已同时支持 HTTP webhook 和 SDK 长连接两种入口
2. 当前实现会返回标准 JSON 结果，适合作为控制层后端验证
3. 配置 `FEISHU_APP_ID`、`FEISHU_APP_SECRET` 后，系统会尝试通过飞书应用消息接口把命令执行结果回发到原 `chat_id`
4. 若未配置飞书应用凭据，则 `command_result` 会被记录为通知日志，但不会真实发回飞书
5. 配置 `FEISHU_ENCRYPT_KEY` 后，会额外校验 `x-lark-request-timestamp`、`x-lark-request-nonce`、`x-lark-signature`
6. 签名校验包含时间窗限制和 Redis 优先、内存兜底的重放保护；`url_verification` challenge 仍允许直接通过
7. 长连接模式通过 `lark-oapi` 官方 SDK 接收 `p2_im_message_receive_v1` 事件，再转入当前 `CommandRouter`

## 手机轻控制页

当前已提供最小手机控制入口：

```text
GET  /mobile/jobs
POST /mobile/jobs
GET  /mobile/jobs/{job_id}
POST /mobile/jobs/{job_id}/action
POST /mobile/logout
GET  /mobile/assets/{asset_id}/preview
```

说明：

1. `GET /mobile/jobs` 提供移动端任务列表和创建表单
2. `POST /mobile/jobs` 使用表单方式创建任务，并重定向到详情页
3. `GET /mobile/jobs/{job_id}` 展示任务状态、后端、素材概览和可执行动作
4. `POST /mobile/jobs/{job_id}/action` 当前支持 `approve`、`retry`、`cancel`
5. `POST /mobile/logout` 用于清除移动端短期 session
6. `GET /mobile/assets/{asset_id}/preview` 用于直接预览已生成素材
7. 配置 `MOBILE_ACCESS_TOKEN` 后，访问 `/mobile/*` 会先跳到 `/mobile/login`，登录成功后写入短期 session cookie
8. 这一层刻意保持无模板引擎、无前端构建依赖，便于直接部署在现有 API 服务中

## 多后端出图建议

推荐的实际使用方式：

1. 把 `comfyui_remote` 作为主后端
   适合你自己的台式机 GPU
2. 把 `third_party` 作为备用后端
   适合台式机不可用或需要快速补图
3. 把 `codex_cli` 作为实验后端
   适合你本人在已登录 ChatGPT/Codex 环境下做本机试验，不建议作为主生产后端
4. 把 `chatgpt_web` 作为半自动稳定后端
   适合你已经有 ChatGPT 网页登录态、接受页面结构偶发波动且希望绕开第三方图片 API 时使用

这意味着：

1. 文本链路共用
2. 只在出图阶段切换后端
3. 不需要为两类出图方式维护两套上游分镜系统

## 运行测试

完整回归：

```bash
pytest -v
```

当前已经覆盖的测试包括：

1. 健康检查 API
2. 配置系统
3. ORM 模型与迁移基础
4. 结构化 Schema
5. LLM Provider
6. 模板渲染与 Prompt 组装
7. 缓存与幂等
8. 大纲/分镜服务
9. ComfyUI 客户端与图像服务
10. 第三方图像 Provider
11. 多后端工厂装配
12. `codex_cli` 实验型图片后端
13. `chatgpt_web` 浏览器自动化图片后端
13. 质量检查
14. 编排服务
15. 成本统计
16. API 行为
17. Worker 执行入口
18. 全链路 Mock e2e
19. 真实 RQ 入队烟测相关路径
20. 运行期健康诊断
21. 非法 `image_backend` 请求校验
22. 飞书通知记录与状态变化通知
23. 飞书命令解析与 webhook 入口
24. 命令 token 校验与命令层审计
25. 飞书应用消息回发与 `command_result` 通知
26. 手机轻控制页与任务动作表单链路
27. 飞书签名校验、时间窗校验与重放保护
28. 手机轻控制页登录与短期 session
29. 飞书长连接命令入口与 SDK 客户端装配

## 当前已知限制

1. Worker 真实消费链仍依赖 Redis、真实 `LLM_API_KEY`、真实 ComfyUI 或第三方 API 可访问。
2. ComfyUI 工作流还是通用结构，未绑定具体节点模板。
3. 第三方图像 API 当前是通用适配层，具体请求体和响应体可能还需按目标供应商细化。
4. 当前还没有按后端区分更细的成本模型。
5. 手机轻控制页当前只适合单用户场景，尚未接入多用户隔离、权限分级和注销管理。
6. 当前飞书命令入口已可执行并返回 JSON；只有配置 `FEISHU_APP_ID` 与 `FEISHU_APP_SECRET` 后，才会真实尝试飞书对话回发。
7. 当前飞书重放保护已升级为 Redis 优先、内存兜底；如果以后做多实例部署，仍建议继续复用同一 Redis 并补监控与过期策略可观测性。
8. 飞书长连接当前只接了 `p2_im_message_receive_v1` 文本消息事件，还没有扩到卡片交互或更复杂事件类型。
9. `codex_cli` 后端依赖本机已安装并登录的 Codex CLI，适合实验和人工参与场景，不建议直接当主生产出图链路。
10. `chatgpt_web` 后端依赖 ChatGPT 网页结构与账号登录态，属于半自动稳定方案；页面改版、未登录或下载按钮变化时会直接报错，不会静默降级。

## 下一步建议

1. 把你的台式机 ComfyUI 固定成 `COMFYUI_BASE_URL`
2. 选一个真实第三方图像 API，细化 `third_party` provider 的字段映射
3. 增加按 `image_backend` 分开的成本统计与重试策略
4. 把 Worker 真正跑起来，做一次真实任务消费验证
5. 给手机轻控制页补结果预览、筛选、退出登录和更细粒度操作保护
6. 把飞书重放保护提升为 Redis 级别，适配多进程或多实例部署
7. 视需要补 Feishu 命令 DSL、异步结果卡片和更细的通知策略
8. 视飞书侧配置决定是否保留 webhook 与长连接双入口并存
9. 如果继续保留 `codex_cli`，建议后续再补配额、耗时和失败分类统计
10. 如果继续强化 `chatgpt_web`，建议后续把选择器探测、失败截图和多站点适配抽成更清晰的 adapter 层

## 最新补充：飞书图片回传与任意 Codex CLI 指令

当前飞书控制层已经额外支持两条能力：

1. 工作流图片回传
   当任务完成并进入 `waiting_review` 后，系统会优先选择首个已生成素材，
   通过飞书应用消息接口上传本地图片，再向原会话发送 `image` 消息。
   这要求已经配置：
   - `FEISHU_APP_ID`
   - `FEISHU_APP_SECRET`
   - 可选 `FEISHU_OPEN_BASE_URL`

2. 任意 Codex CLI 任务
   飞书里现在支持直接下发 `codex` 任务，不再局限于白名单工作流动作。
   当前实现走的是 `codex exec` 的任意 prompt 执行链路，而不是任意 shell。
   这能满足“飞书里让 Codex CLI 处理任意任务”和“飞书里触发既定工作流”并存。

新增命令：

```text
/codex prompt="Inspect this repo and reply with exactly one line: OK"
/codex Inspect this repo and reply with exactly one line: OK
/new
/codex_status run=12
```

说明：
1. `/codex` 会创建一条 `CodexRun` 记录并异步入队
2. Worker 会调用本机 `codex exec`
3. 执行结果会回发到原飞书会话
4. 如果本次 Codex 任务产生了图片，系统也会尝试把图片上传并回发到飞书
5. `/codex_status` 可查询指定 `run_id` 的当前状态、结果摘要和输出文件路径

当前推荐用法：
1. 飞书工作流任务继续用 `/create ... backend=codex_cli|third_party|comfyui_remote|chatgpt_web`
2. 任意 Codex 任务可以直接发普通文本，例如 `Read README and tell me the current blockers`
3. 如果你仍想显式指定，也可以用 `/codex prompt="..."` 或 `/codex 直接写任务内容`
4. 需要追踪时用 `/status job=...` 或 `/codex_status run=...`

飞书自然语言入口规则：
1. 以 `/create`、`/status`、`/retry`、`/approve`、`/cancel`、`/assets`、`/health`、`/codex_status` 开头的消息，按显式命令处理
2. 以 `/codex` 开头的消息，按显式 Codex 任务处理
3. 不以 `/` 开头的普通文本，默认整体作为一条 `codex exec` prompt
4. `/new` 用于手动重置当前 `chat_id` 的共享 Codex 会话
5. 这意味着你现在可以把飞书当成 Codex CLI 的自然语言远程入口，而工作流类动作仍然通过显式 `/create` 等命令触发

正式会话规则：
1. 普通文本和 `/codex` 会进入按 `chat_id` 共享的正式会话
2. `/create`、`/status`、`/retry`、`/approve`、`/cancel`、`/assets`、`/health`、`/codex_status` 不进入会话历史
3. 同一个 `chat_id` 空闲超过 `CONVERSATION_IDLE_TIMEOUT_SECONDS` 后，会自动切到新会话
4. 当会话消息过长时，系统会把更早消息压缩成摘要，只保留最近若干条原文消息
5. 当前底层仍然是每次新起一次 `codex exec`，但会话层会把摘要和最近消息组装成连续上下文
