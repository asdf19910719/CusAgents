# Custom Agents

一个面向内容生成流水线的最小可运行服务骨架，当前已经支持两类出图后端：

1. `comfyui_remote`
   当前项目通过 HTTP API 调用另一台机器或本机上的 ComfyUI
2. `third_party`
   当前项目通过第三方图像 API 出图

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
7. `pytest`

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
16. `AUTO_ENQUEUE_JOBS`
17. `QUEUE_NAME`

说明：

1. `IMAGE_BACKEND` 是系统默认出图后端
2. 每个 `Job` 也可以单独指定 `image_backend`
3. 当前支持值：
   `comfyui_remote`
   `third_party`
4. `FEISHU_NOTIFY_WEBHOOK_URL` 配置后，系统会在任务创建、等待审核、失败等事件写通知日志，并尝试推送飞书 webhook
5. `FEISHU_VERIFICATION_TOKEN` 用于飞书事件入口的最小 token 校验

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

这个接口会返回数据库、Redis、LLM 配置、`comfyui_remote`、`third_party` 的当前状态，适合联调前快速判断是配置缺失、服务不可达，还是队列未开启。

## 启动 Worker

当前 Worker 依赖本地可用的 Redis：

```bash
python scripts/run_worker.py
```

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
```

当前 `POST /jobs` 返回中会包含：

1. `dispatch_status`
2. `queue_name`
3. `dispatch_error`

`image_backend` 只接受：

1. `comfyui_remote`
2. `third_party`

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

1. 当前入口按飞书事件回调格式接收文本消息
2. 当前实现会返回标准 JSON 结果，适合作为控制层后端验证
3. 配置 `FEISHU_APP_ID`、`FEISHU_APP_SECRET` 后，系统会尝试通过飞书应用消息接口把命令执行结果回发到原 `chat_id`
4. 若未配置飞书应用凭据，则 `command_result` 会被记录为通知日志，但不会真实发回飞书

## 多后端出图建议

推荐的实际使用方式：

1. 把 `comfyui_remote` 作为主后端
   适合你自己的台式机 GPU
2. 把 `third_party` 作为备用后端
   适合台式机不可用或需要快速补图

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
12. 质量检查
13. 编排服务
14. 成本统计
15. API 行为
16. Worker 执行入口
17. 全链路 Mock e2e
18. 真实 RQ 入队烟测相关路径
19. 运行期健康诊断
20. 非法 `image_backend` 请求校验
21. 飞书通知记录与状态变化通知
22. 飞书命令解析与 webhook 入口
23. 命令 token 校验与命令层审计
24. 飞书应用消息回发与 `command_result` 通知

## 当前已知限制

1. Worker 真实消费链仍依赖 Redis、真实 `LLM_API_KEY`、真实 ComfyUI 或第三方 API 可访问。
2. ComfyUI 工作流还是通用结构，未绑定具体节点模板。
3. 第三方图像 API 当前是通用适配层，具体请求体和响应体可能还需按目标供应商细化。
4. 当前还没有按后端区分更细的成本模型。
5. 当前只完成了飞书通知出口，尚未实现飞书命令入口和手机控制页。
6. 当前飞书命令入口已可执行并返回 JSON；只有配置 `FEISHU_APP_ID` 与 `FEISHU_APP_SECRET` 后，才会真实尝试飞书对话回发。

## 下一步建议

1. 把你的台式机 ComfyUI 固定成 `COMFYUI_BASE_URL`
2. 选一个真实第三方图像 API，细化 `third_party` provider 的字段映射
3. 增加按 `image_backend` 分开的成本统计与重试策略
4. 把 Worker 真正跑起来，做一次真实任务消费验证
5. 按控制层方案继续补飞书命令入口与手机轻控制页
6. 补飞书应用消息回发与更完整的签名校验
7. 继续做手机轻控制页与更完整的飞书签名校验
