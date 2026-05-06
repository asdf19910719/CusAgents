# 自定义 Agents 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一套可维护、可扩展、可追踪成本的自定义 Agents 内容生成系统，围绕“需求输入 -> 故事大纲 -> 分镜结构化 -> Prompt 组装 -> 图像生成 -> 质量检查 -> 人工审核”形成最小可运行闭环。

**Architecture:** 采用 `FastAPI + SQLAlchemy + Redis + RQ + ComfyUI API` 的服务化架构。核心思路是把强模型调用限制在高价值阶段，把中间产物结构化并持久化，用任务队列、缓存、幂等键、成本统计和质量检查支撑后续批量任务与多 Agent 扩展。

**Tech Stack:** Python 3.11、FastAPI、Pydantic v2、SQLAlchemy 2.x、Alembic、SQLite（开发）/ PostgreSQL（生产）、Redis、RQ、httpx、Jinja2、pytest、ComfyUI HTTP API。

---

## 一、计划使用方式

这份文档不是泛化讨论稿，而是给后续 AI 或工程实现者直接执行的实施计划。

执行原则如下：

1. 先做最小可运行链路，再做优化能力。
2. 先保证结构化输出和状态可追踪，再做多模型替换。
3. 每个任务结束后，必须能留下可验证成果。
4. 每个阶段都必须有最小测试，不接受“先写完再统一补测试”。

---

## 二、默认实现边界

为避免后续 AI 发散，先固定以下默认边界。

### 1. 明确采用的默认技术选择

1. 后端服务：FastAPI
2. 数据存储：开发环境 SQLite，生产环境 PostgreSQL
3. 缓存与队列：Redis
4. 后台任务执行：RQ Worker
5. LLM 访问方式：统一 Provider 抽象层，默认先接 OpenAI 兼容接口
6. 图像生成：ComfyUI HTTP API
7. 模板渲染：Jinja2
8. 测试框架：pytest

### 2. 本期不做的内容

1. 不做复杂前端页面，只提供 API 和基础管理接口。
2. 不做多租户。
3. 不做完整权限系统，只预留简单 API Key 或单用户模式。
4. 不做自动视频剪辑，仅覆盖文本到图像素材链路。
5. 不接网页自动化方案作为主流程。

### 3. 必须满足的验收目标

1. 能提交一个内容生成任务。
2. 能自动生成故事大纲、分镜结构和图像 Prompt。
3. 能调用 ComfyUI 生成图片并保存元数据。
4. 能记录每一步的状态、耗时、成本和失败原因。
5. 能对中间结果做缓存、局部重试和人工审核。

---

## 三、推荐目录结构

后续实现统一按下面目录开始，不要自行发散成多套风格。

```text
project-root/
├─ app/
│  ├─ main.py
│  ├─ api/
│  │  ├─ routes/
│  │  │  ├─ health.py
│  │  │  ├─ jobs.py
│  │  │  ├─ assets.py
│  │  │  └─ admin.py
│  │  └─ deps.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ logging.py
│  │  ├─ enums.py
│  │  └─ ids.py
│  ├─ db/
│  │  ├─ base.py
│  │  ├─ session.py
│  │  └─ models/
│  │     ├─ job.py
│  │     ├─ step_run.py
│  │     ├─ llm_cache.py
│  │     ├─ prompt_template.py
│  │     ├─ asset.py
│  │     └─ review.py
│  ├─ schemas/
│  │  ├─ common.py
│  │  ├─ job.py
│  │  ├─ storyboard.py
│  │  ├─ prompt.py
│  │  └─ review.py
│  ├─ providers/
│  │  ├─ llm/
│  │  │  ├─ base.py
│  │  │  ├─ openai_compatible.py
│  │  │  └─ factory.py
│  │  └─ image/
│  │     ├─ comfyui_client.py
│  │     └─ workflow_builder.py
│  ├─ services/
│  │  ├─ idempotency_service.py
│  │  ├─ cache_service.py
│  │  ├─ prompt_service.py
│  │  ├─ outline_service.py
│  │  ├─ storyboard_service.py
│  │  ├─ image_service.py
│  │  ├─ quality_service.py
│  │  ├─ cost_service.py
│  │  └─ orchestration_service.py
│  ├─ workers/
│  │  ├─ queue.py
│  │  ├─ jobs.py
│  │  └─ runner.py
│  └─ templates/
│     ├─ outline/
│     │  └─ v1.j2
│     ├─ storyboard/
│     │  └─ v1.j2
│     └─ prompt/
│        └─ v1.j2
├─ migrations/
├─ tests/
│  ├─ api/
│  ├─ services/
│  ├─ providers/
│  └─ e2e/
├─ scripts/
│  ├─ seed_templates.py
│  └─ run_worker.py
├─ .env.example
├─ requirements.txt
└─ README.md
```

---

## 四、核心数据流

系统主流程固定为：

```text
用户提交 Job
  ->
生成幂等键并落库
  ->
故事大纲生成
  ->
分镜结构化生成
  ->
Prompt 组装
  ->
ComfyUI 出图
  ->
质量检查
  ->
人工审核/通过
```

每一步都必须：

1. 有独立状态。
2. 可单独记录输入与输出摘要。
3. 可失败重试。
4. 可统计成本。
5. 可决定是否命中缓存。

---

## 五、核心数据模型定义

后续实现时，先按下面数据实体建模。

### 1. Job

表示一个完整生成任务。

关键字段：

1. `id`
2. `request_id`
3. `topic`
4. `style_preset`
5. `target_shot_count`
6. `status`
7. `idempotency_key`
8. `current_step`
9. `total_input_tokens`
10. `total_output_tokens`
11. `total_cost`
12. `error_message`
13. `created_at`
14. `updated_at`

### 2. StepRun

记录每一步执行结果。

关键字段：

1. `id`
2. `job_id`
3. `step_name`
4. `attempt_no`
5. `status`
6. `provider_name`
7. `model_name`
8. `cache_hit`
9. `input_summary`
10. `output_summary`
11. `input_tokens`
12. `output_tokens`
13. `cost`
14. `latency_ms`
15. `error_message`
16. `started_at`
17. `finished_at`

### 3. LlmCache

用于中间结果复用。

关键字段：

1. `cache_key`
2. `step_name`
3. `model_name`
4. `prompt_version`
5. `schema_version`
6. `normalized_input_hash`
7. `response_payload`
8. `created_at`

### 4. PromptTemplate

模板版本管理。

关键字段：

1. `template_name`
2. `template_version`
3. `step_name`
4. `content`
5. `is_active`

### 5. Asset

记录图像产物。

关键字段：

1. `id`
2. `job_id`
3. `shot_index`
4. `prompt_text`
5. `negative_prompt`
6. `seed`
7. `workflow_json`
8. `file_path`
9. `preview_path`
10. `status`

### 6. Review

记录质量检查和人工审核结果。

关键字段：

1. `id`
2. `job_id`
3. `review_type`
4. `result`
5. `score`
6. `notes`
7. `reviewed_by`
8. `created_at`

---

## 六、API 设计边界

初版 API 只做必要接口，避免扩散。

### 1. 健康检查

1. `GET /health`

### 2. Job 管理

1. `POST /jobs`
2. `GET /jobs/{job_id}`
3. `GET /jobs/{job_id}/steps`
4. `POST /jobs/{job_id}/retry`
5. `POST /jobs/{job_id}/approve`
6. `POST /jobs/{job_id}/cancel`

### 3. 产物查看

1. `GET /jobs/{job_id}/assets`
2. `GET /assets/{asset_id}`

### 4. 管理接口

1. `GET /admin/templates`
2. `POST /admin/templates`
3. `POST /admin/cache/clear`
4. `GET /admin/stats/cost`

---

## 七、阶段化实施任务

下面任务按顺序执行。没有必要并行的阶段，不要强行并行。

### Task 1：初始化项目骨架

**Files:**
- Create: `project-root/requirements.txt`
- Create: `project-root/app/main.py`
- Create: `project-root/app/core/config.py`
- Create: `project-root/app/core/logging.py`
- Create: `project-root/README.md`
- Create: `project-root/.env.example`

- [ ] **Step 1：创建基础依赖清单**

```txt
fastapi
uvicorn[standard]
pydantic
pydantic-settings
sqlalchemy
alembic
redis
rq
httpx
jinja2
pytest
pytest-asyncio
```

- [ ] **Step 2：创建应用入口**

```python
from fastapi import FastAPI

app = FastAPI(title="Custom Agents")


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 3：运行服务验证骨架**

Run: `uvicorn app.main:app --reload`

Expected: 打开 `http://127.0.0.1:8000/health` 返回 `{"status":"ok"}`。

- [ ] **Step 4：提交本任务改动**

```bash
git add requirements.txt app/main.py app/core/config.py app/core/logging.py README.md .env.example
git commit -m "chore: initialize custom agents service skeleton"
```

### Task 2：配置系统与环境变量

**Files:**
- Modify: `project-root/app/core/config.py`
- Modify: `project-root/.env.example`
- Create: `project-root/tests/services/test_config.py`

- [ ] **Step 1：定义配置模型**

必须包含：

1. `APP_ENV`
2. `DATABASE_URL`
3. `REDIS_URL`
4. `LLM_BASE_URL`
5. `LLM_API_KEY`
6. `LLM_DEFAULT_MODEL`
7. `COMFYUI_BASE_URL`
8. `OUTPUT_DIR`

- [ ] **Step 2：写配置测试**

测试目标：

1. 默认值可加载。
2. 缺失关键变量时抛出明确错误。
3. `SQLite` 与 `PostgreSQL` 连接字符串都可被解析。

- [ ] **Step 3：运行配置测试**

Run: `pytest tests/services/test_config.py -v`

Expected: 全部通过。

- [ ] **Step 4：提交本任务改动**

```bash
git add app/core/config.py .env.example tests/services/test_config.py
git commit -m "feat: add settings and environment configuration"
```

### Task 3：数据库层与迁移初始化

**Files:**
- Create: `project-root/app/db/base.py`
- Create: `project-root/app/db/session.py`
- Create: `project-root/app/db/models/job.py`
- Create: `project-root/app/db/models/step_run.py`
- Create: `project-root/app/db/models/llm_cache.py`
- Create: `project-root/app/db/models/prompt_template.py`
- Create: `project-root/app/db/models/asset.py`
- Create: `project-root/app/db/models/review.py`
- Create: `project-root/migrations/`
- Create: `project-root/tests/services/test_models.py`

- [ ] **Step 1：创建基础 ORM 基类与会话工厂**

要求：

1. 提供统一 `Base`。
2. 提供 `SessionLocal`。
3. 兼容 SQLite 与 PostgreSQL。

- [ ] **Step 2：按本计划定义六个核心模型**

要求：

1. 状态字段统一枚举。
2. 金额字段统一数值精度。
3. JSON 载荷字段支持缓存结果和工作流元数据。

- [ ] **Step 3：初始化 Alembic 并生成首个迁移**

Run: `alembic revision --autogenerate -m "init core tables"`

Expected: 生成首个迁移脚本，包含核心表。

- [ ] **Step 4：模型测试**

Run: `pytest tests/services/test_models.py -v`

Expected: 能创建 `Job`、`StepRun`、`LlmCache`、`Asset` 记录并完成基本关联。

- [ ] **Step 5：提交本任务改动**

```bash
git add app/db migrations tests/services/test_models.py
git commit -m "feat: add core database schema and migrations"
```

### Task 4：定义 Schema 与结构化输出契约

**Files:**
- Create: `project-root/app/schemas/common.py`
- Create: `project-root/app/schemas/job.py`
- Create: `project-root/app/schemas/storyboard.py`
- Create: `project-root/app/schemas/prompt.py`
- Create: `project-root/app/schemas/review.py`
- Create: `project-root/tests/services/test_schemas.py`

- [ ] **Step 1：定义 Storyboard 结构**

每个镜头至少包含：

1. `shot_index`
2. `scene`
3. `subject`
4. `action`
5. `camera`
6. `lighting`
7. `emotion`
8. `duration_hint`

- [ ] **Step 2：定义 Prompt 结构**

至少包含：

1. `positive_prompt`
2. `negative_prompt`
3. `style_tags`
4. `shot_index`

- [ ] **Step 3：写结构校验测试**

Run: `pytest tests/services/test_schemas.py -v`

Expected: 非法字段、缺失字段、镜头顺序错误都被拦截。

- [ ] **Step 4：提交本任务改动**

```bash
git add app/schemas tests/services/test_schemas.py
git commit -m "feat: add domain schemas for jobs storyboard and prompts"
```

### Task 5：LLM Provider 抽象层

**Files:**
- Create: `project-root/app/providers/llm/base.py`
- Create: `project-root/app/providers/llm/openai_compatible.py`
- Create: `project-root/app/providers/llm/factory.py`
- Create: `project-root/tests/providers/test_llm_provider.py`

- [ ] **Step 1：定义统一 Provider 接口**

接口最少包含：

1. `generate_text()`
2. `generate_structured()`
3. `estimate_cost()`

- [ ] **Step 2：实现 OpenAI 兼容 Provider**

要求：

1. 支持文本输出。
2. 支持结构化 JSON 输出。
3. 解析 token 用量。
4. 返回统一结果对象。

- [ ] **Step 3：写 Provider 测试**

使用 mock 响应验证：

1. 文本返回解析正确。
2. 结构化返回可落到 Pydantic Schema。
3. token 和 cost 信息能被提取。

- [ ] **Step 4：提交本任务改动**

```bash
git add app/providers/llm tests/providers/test_llm_provider.py
git commit -m "feat: add llm provider abstraction"
```

### Task 6：模板与 Prompt 渲染能力

**Files:**
- Create: `project-root/app/services/prompt_service.py`
- Create: `project-root/app/templates/outline/v1.j2`
- Create: `project-root/app/templates/storyboard/v1.j2`
- Create: `project-root/app/templates/prompt/v1.j2`
- Create: `project-root/scripts/seed_templates.py`
- Create: `project-root/tests/services/test_prompt_service.py`

- [ ] **Step 1：写三类模板**

模板必须分别覆盖：

1. 故事大纲生成。
2. 分镜结构化生成。
3. Prompt 组装。

- [ ] **Step 2：实现模板渲染服务**

要求：

1. 支持模板版本选择。
2. 渲染前检查必须字段。
3. 渲染结果可用于缓存键计算。

- [ ] **Step 3：种子脚本初始化模板**

Run: `python scripts/seed_templates.py`

Expected: 模板被写入数据库或本地版本登记表。

- [ ] **Step 4：模板测试**

Run: `pytest tests/services/test_prompt_service.py -v`

Expected: 渲染结果稳定、参数缺失时报错明确。

- [ ] **Step 5：提交本任务改动**

```bash
git add app/services/prompt_service.py app/templates scripts/seed_templates.py tests/services/test_prompt_service.py
git commit -m "feat: add versioned prompt template system"
```

### Task 7：缓存与幂等机制

**Files:**
- Create: `project-root/app/services/cache_service.py`
- Create: `project-root/app/services/idempotency_service.py`
- Create: `project-root/tests/services/test_cache_service.py`
- Create: `project-root/tests/services/test_idempotency_service.py`

- [ ] **Step 1：实现缓存键规范**

缓存键至少组合：

1. `step_name`
2. `normalized_input_hash`
3. `model_name`
4. `prompt_version`
5. `schema_version`

- [ ] **Step 2：实现幂等键服务**

要求：

1. 同输入重复提交可复用已有 Job。
2. 允许显式跳过幂等。
3. 幂等命中时返回旧任务信息。

- [ ] **Step 3：缓存与幂等测试**

Run: `pytest tests/services/test_cache_service.py tests/services/test_idempotency_service.py -v`

Expected: 相同请求命中，相同内容不同模板版本不误命中。

- [ ] **Step 4：提交本任务改动**

```bash
git add app/services/cache_service.py app/services/idempotency_service.py tests/services/test_cache_service.py tests/services/test_idempotency_service.py
git commit -m "feat: add cache and idempotency services"
```

### Task 8：故事大纲与分镜服务

**Files:**
- Create: `project-root/app/services/outline_service.py`
- Create: `project-root/app/services/storyboard_service.py`
- Create: `project-root/tests/services/test_outline_service.py`
- Create: `project-root/tests/services/test_storyboard_service.py`

- [ ] **Step 1：实现故事大纲服务**

要求：

1. 输入主题、风格、镜头数量。
2. 调用强模型生成摘要式故事骨架。
3. 写入 `StepRun` 成本信息。
4. 先查缓存，再决定是否调用模型。

- [ ] **Step 2：实现分镜服务**

要求：

1. 基于故事骨架生成结构化镜头列表。
2. 输出必须能通过 `StoryboardSchema` 校验。
3. 校验失败时保留错误摘要。

- [ ] **Step 3：服务测试**

Run: `pytest tests/services/test_outline_service.py tests/services/test_storyboard_service.py -v`

Expected: 缓存命中、生成功能、结构校验、失败记录全部通过。

- [ ] **Step 4：提交本任务改动**

```bash
git add app/services/outline_service.py app/services/storyboard_service.py tests/services/test_outline_service.py tests/services/test_storyboard_service.py
git commit -m "feat: add outline and storyboard generation services"
```

### Task 9：Prompt 组装服务

**Files:**
- Modify: `project-root/app/services/prompt_service.py`
- Create: `project-root/tests/services/test_prompt_pipeline.py`

- [ ] **Step 1：实现按镜头生成 Prompt**

要求：

1. 每个镜头产出一组 `positive_prompt` 和 `negative_prompt`。
2. 支持风格预设。
3. 支持模板版本切换。

- [ ] **Step 2：增加 Prompt 结果持久化策略**

结果至少要能被：

1. 后续出图读取。
2. 缓存复用。
3. 人工审核查看。

- [ ] **Step 3：Prompt 链路测试**

Run: `pytest tests/services/test_prompt_pipeline.py -v`

Expected: 一个 3 镜头输入能稳定产出 3 组结构化 Prompt。

- [ ] **Step 4：提交本任务改动**

```bash
git add app/services/prompt_service.py tests/services/test_prompt_pipeline.py
git commit -m "feat: add prompt assembly pipeline"
```

### Task 10：ComfyUI 客户端与工作流组装

**Files:**
- Create: `project-root/app/providers/image/comfyui_client.py`
- Create: `project-root/app/providers/image/workflow_builder.py`
- Create: `project-root/app/services/image_service.py`
- Create: `project-root/tests/providers/test_comfyui_client.py`
- Create: `project-root/tests/services/test_image_service.py`

- [ ] **Step 1：实现 ComfyUI 客户端**

能力至少包含：

1. 提交工作流。
2. 查询任务状态。
3. 下载结果图。

- [ ] **Step 2：实现工作流构造器**

要求：

1. 根据 Prompt、种子、风格预设生成工作流 JSON。
2. 支持默认采样器和尺寸配置。
3. 保留可扩展节点参数入口。

- [ ] **Step 3：实现图像生成服务**

要求：

1. 逐镜头生成。
2. 保存 `workflow_json` 和 `seed`。
3. 失败时能写 `Asset.status=failed`。

- [ ] **Step 4：图像链路测试**

Run: `pytest tests/providers/test_comfyui_client.py tests/services/test_image_service.py -v`

Expected: Mock 情况下能完成工作流提交、状态轮询和资产记录。

- [ ] **Step 5：提交本任务改动**

```bash
git add app/providers/image app/services/image_service.py tests/providers/test_comfyui_client.py tests/services/test_image_service.py
git commit -m "feat: add comfyui integration and asset generation"
```

### Task 11：任务编排与状态机

**Files:**
- Create: `project-root/app/services/orchestration_service.py`
- Create: `project-root/app/core/enums.py`
- Create: `project-root/tests/services/test_orchestration_service.py`

- [ ] **Step 1：定义任务状态流转**

最少包括：

1. `pending`
2. `running`
3. `waiting_review`
4. `completed`
5. `failed`
6. `cancelled`

- [ ] **Step 2：实现编排器**

职责：

1. 串联 outline、storyboard、prompt、image、quality 五步。
2. 统一写 `StepRun`。
3. 发生异常时更新 `Job.status` 与 `current_step`。
4. 支持从失败步骤继续。

- [ ] **Step 3：状态机测试**

Run: `pytest tests/services/test_orchestration_service.py -v`

Expected: 正常流转、失败中断、从中间步骤恢复都能验证。

- [ ] **Step 4：提交本任务改动**

```bash
git add app/services/orchestration_service.py app/core/enums.py tests/services/test_orchestration_service.py
git commit -m "feat: add job orchestration and state management"
```

### Task 12：队列、Worker 与重试执行

**Files:**
- Create: `project-root/app/workers/queue.py`
- Create: `project-root/app/workers/jobs.py`
- Create: `project-root/app/workers/runner.py`
- Create: `project-root/scripts/run_worker.py`
- Create: `project-root/tests/e2e/test_worker_flow.py`

- [ ] **Step 1：创建 RQ 队列封装**

要求：

1. 有默认队列名。
2. 支持延迟重试。
3. 支持记录重试次数。

- [ ] **Step 2：实现 Worker Job 入口**

职责：

1. 接收 `job_id`。
2. 调用编排器。
3. 捕获异常并写回数据库。

- [ ] **Step 3：增加本地运行脚本**

Run: `python scripts/run_worker.py`

Expected: Worker 成功连接 Redis 并等待任务。

- [ ] **Step 4：端到端 Worker 测试**

Run: `pytest tests/e2e/test_worker_flow.py -v`

Expected: 提交任务后 Worker 可消费并完成至少一个完整 Mock 流程。

- [ ] **Step 5：提交本任务改动**

```bash
git add app/workers scripts/run_worker.py tests/e2e/test_worker_flow.py
git commit -m "feat: add background worker and retry execution"
```

### Task 13：质量检查与人工审核

**Files:**
- Create: `project-root/app/services/quality_service.py`
- Create: `project-root/app/schemas/review.py`
- Create: `project-root/tests/services/test_quality_service.py`

- [ ] **Step 1：定义规则检查**

至少检查：

1. 分镜字段是否完整。
2. Prompt 是否为空。
3. 产物数量是否与镜头数一致。

- [ ] **Step 2：定义模型辅助检查接口**

先只保留接口，不必做复杂视觉理解，但必须支持：

1. 后续接入 LLM 评估。
2. 记录评分和备注。

- [ ] **Step 3：人工审核入口设计**

要求：

1. `Job` 通过质量检查后可进入 `waiting_review`。
2. 审核通过后进入 `completed`。
3. 审核拒绝后允许回退重试。

- [ ] **Step 4：质量与审核测试**

Run: `pytest tests/services/test_quality_service.py -v`

Expected: 规则检查、审核通过、审核拒绝三类路径都能验证。

- [ ] **Step 5：提交本任务改动**

```bash
git add app/services/quality_service.py app/schemas/review.py tests/services/test_quality_service.py
git commit -m "feat: add quality checks and review flow"
```

### Task 14：成本统计与观测能力

**Files:**
- Create: `project-root/app/services/cost_service.py`
- Modify: `project-root/app/core/logging.py`
- Create: `project-root/tests/services/test_cost_service.py`

- [ ] **Step 1：实现成本聚合服务**

至少统计：

1. 单步成本。
2. 单任务总成本。
3. 输入输出 token 总量。
4. 失败步骤平均成本。

- [ ] **Step 2：标准化结构日志**

每次步骤执行至少记录：

1. `job_id`
2. `step_name`
3. `status`
4. `latency_ms`
5. `cost`
6. `cache_hit`

- [ ] **Step 3：成本测试**

Run: `pytest tests/services/test_cost_service.py -v`

Expected: 多个 `StepRun` 能被正确汇总到任务级成本。

- [ ] **Step 4：提交本任务改动**

```bash
git add app/services/cost_service.py app/core/logging.py tests/services/test_cost_service.py
git commit -m "feat: add cost aggregation and structured logging"
```

### Task 15：API 路由与管理接口

**Files:**
- Create: `project-root/app/api/deps.py`
- Create: `project-root/app/api/routes/health.py`
- Create: `project-root/app/api/routes/jobs.py`
- Create: `project-root/app/api/routes/assets.py`
- Create: `project-root/app/api/routes/admin.py`
- Modify: `project-root/app/main.py`
- Create: `project-root/tests/api/test_jobs_api.py`
- Create: `project-root/tests/api/test_admin_api.py`

- [ ] **Step 1：实现 Job 提交与查询接口**

要求：

1. `POST /jobs` 创建任务。
2. `GET /jobs/{job_id}` 返回任务状态和摘要。
3. `GET /jobs/{job_id}/steps` 返回步骤记录。

- [ ] **Step 2：实现重试与审核接口**

要求：

1. `POST /jobs/{job_id}/retry`
2. `POST /jobs/{job_id}/approve`
3. `POST /jobs/{job_id}/cancel`

- [ ] **Step 3：实现管理接口**

至少支持：

1. 查看模板版本。
2. 查看成本统计。
3. 清理缓存。

- [ ] **Step 4：API 测试**

Run: `pytest tests/api/test_jobs_api.py tests/api/test_admin_api.py -v`

Expected: 创建任务、查询任务、重试任务、审核通过都能跑通。

- [ ] **Step 5：提交本任务改动**

```bash
git add app/api app/main.py tests/api/test_jobs_api.py tests/api/test_admin_api.py
git commit -m "feat: add public and admin api routes"
```

### Task 16：端到端联调、文档与交付

**Files:**
- Modify: `project-root/README.md`
- Create: `project-root/tests/e2e/test_full_pipeline.py`
- Create: `project-root/scripts/demo_request.py`

- [ ] **Step 1：写最小演示脚本**

脚本行为：

1. 创建一个 Job。
2. 轮询状态。
3. 打印最终资产路径和总成本。

- [ ] **Step 2：补充 README**

至少写清：

1. 环境变量。
2. 本地启动方式。
3. Worker 启动方式。
4. 如何提交一个测试任务。
5. 当前已知限制。

- [ ] **Step 3：端到端测试**

Run: `pytest tests/e2e/test_full_pipeline.py -v`

Expected: 在 Mock LLM 和 Mock ComfyUI 条件下，完整链路通过。

- [ ] **Step 4：回归测试**

Run: `pytest -v`

Expected: 所有测试通过。

- [ ] **Step 5：提交本任务改动**

```bash
git add README.md tests/e2e/test_full_pipeline.py scripts/demo_request.py
git commit -m "docs: finalize implementation guide and demo flow"
```

---

## 八、实现阶段里必须坚持的规则

后续 AI 执行时必须遵守下面规则，否则很容易把系统做坏。

### 1. 不允许跳过结构化输出

故事大纲可以是文本，但分镜和 Prompt 产物必须是结构化对象，不接受只存大段自由文本。

### 2. 不允许把全流程强行压成一次模型调用

大纲、分镜、Prompt、出图必须分步可追踪。允许优化边界，不允许失去中间结果。

### 3. 不允许缺失成本记录

所有 LLM 步骤必须写入 token 和 cost。拿不到官方 cost 时，也要至少记录 token 与模型名。

### 4. 不允许没有失败恢复能力

任何一步失败都必须能够：

1. 标记失败原因。
2. 从失败节点重试。
3. 避免整单任务从头重跑。

### 5. 不允许把模板版本写死在代码里

模板必须有版本概念，并可从数据库或文件系统切换。

---

## 九、里程碑验收

### 里程碑 1：最小闭环

通过标准：

1. 可以创建 Job。
2. 可以跑通大纲、分镜、Prompt 三步。
3. 所有中间结果可查询。

### 里程碑 2：可生成素材

通过标准：

1. 可以调用 ComfyUI 完成出图。
2. 每个镜头都有资产记录。
3. 失败镜头可单独重试。

### 里程碑 3：可用于日常试运行

通过标准：

1. 有缓存。
2. 有幂等。
3. 有成本统计。
4. 有人工审核。

### 里程碑 4：可准备扩展

通过标准：

1. 模板可版本化。
2. 模型 Provider 可替换。
3. SQLite 可切 PostgreSQL。
4. Worker 可支持多进程扩展。

---

## 十、后续扩展预留点

本期不实现，但设计时必须预留接口：

1. 多模型路由策略。
2. 多风格预设中心。
3. 自动视频拼接。
4. 审核后台页面。
5. 多租户与配额。
6. 更复杂的质量评估，例如角色一致性和视觉相似度检查。

---

## 十一、最终建议

后续 AI 若按照本文档实现，不要擅自改成“单脚本一把梭”的结构。即使原型能快一点，也会直接损失缓存、重试、审计和可维护性。

最稳妥的执行方式是：

1. 严格按 Task 1 到 Task 16 顺序推进。
2. 每个任务结束必须跑对应测试。
3. 每个任务结束保留清晰提交点。
4. 先完成 Mock 链路，再接真实模型与真实 ComfyUI。

只要按这个边界执行，后续 AI 基本可以在不重新做架构决策的情况下直接进入实现阶段。
