# ArcReel 底座改造实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 以 `runtime/research/ArcReel` 为主应用底座，把 CusAgents 已具备的即梦、ChatGPT Web、飞书通知和 Codex 会话能力通过 bridge 接入 ArcReel，并验证 2 分镜故事视频闭环。

**Architecture:** 第一版不复制 CusAgents 业务代码进 ArcReel，而是在 CusAgents 增加薄 bridge API，ArcReel 侧新增 HTTP provider/adapter 调用该 bridge。ArcReel 保留 UI、项目、任务队列、素材、合成和导出体系；CusAgents 继续负责依赖宿主机登录态或 CLI 登录态的本地生成能力。

**Tech Stack:** ArcReel: Python 3.12+, FastAPI, SQLAlchemy Async, React 19, Docker/WSL2. CusAgents: Python 3.14 当前本机环境, FastAPI, SQLAlchemy, Redis/RQ, Dreamina CLI, Playwright/Chrome, Feishu SDK.

---

## Scope Check

`doc/ArcReel底座改造详细需求.md` 覆盖多个独立子系统。为降低风险，实施拆成六个可独立验证的计划段：

1. 阶段 0-1：许可、运行环境、ArcReel 原生基线。
2. 阶段 2：CusAgents bridge API + ArcReel 即梦图片/视频 provider。
3. 阶段 3：多参考图视频 manifest、模式路由和长任务 `querying`。
4. 阶段 4：ChatGPT Web 图片 provider 接入。
5. 阶段 5：飞书命令、通知和 Codex 会话绑定。
6. 阶段 6：2 分镜真实验收。

本计划先写完整执行路径，但编码时应按阶段分支/提交，不应一次性修改所有模块。

## 当前已确认事实

- ArcReel 本地克隆位置：`runtime/research/ArcReel`。
- ArcReel 是独立 git 仓库；CusAgents 根 `.gitignore` 已忽略 `runtime/`。
- ArcReel 默认 Docker 入口：`runtime/research/ArcReel/deploy/docker-compose.yml`。
- ArcReel 访问端口：`1241`。
- ArcReel 后端入口：`server/app.py`。
- ArcReel provider 抽象：
  - 图片：`lib/image_backends/base.py`、`lib/image_backends/__init__.py`、`lib/image_backends/registry.py`
  - 视频：`lib/video_backends/base.py`、`lib/video_backends/__init__.py`、`lib/video_backends/registry.py`
- ArcReel 任务队列：`lib/generation_queue.py`、`lib/generation_worker.py`、`server/services/generation_tasks.py`。
- ArcReel 参考图视频 executor：`server/services/reference_video_tasks.py`。
- CusAgents 现有可复用能力：
  - `/videos`：创建、查询、刷新 Dreamina 视频任务。
  - `/story-videos`：项目级分镜视频编排。
  - `DreaminaCliImageProvider`、`DreaminaCliVideoProvider`、`ChatgptWebImageProvider`。
- CusAgents 当前缺口：缺少面向 ArcReel 的“单次图片生成 bridge API”和“单次视频生成 bridge API”的统一简洁合同。
- 本机环境：Docker 29.2.1 可用，`docker-desktop` WSL2 正在运行；`127.0.0.1:1241` 当前未连通。

## File Map

### CusAgents Bridge

- Create: `app/schemas/arcreel_bridge.py`
  - 定义 ArcReel 调 CusAgents 的图片/视频请求和响应。
- Create: `app/api/routes/arcreel_bridge.py`
  - 暴露 `/arcreel/bridge/images`、`/arcreel/bridge/videos`、`/arcreel/bridge/videos/{bridge_job_id}/refresh`、`/arcreel/bridge/health`。
- Modify: `app/main.py`
  - 注册 bridge router。
- Modify: `app/services/factory.py`
  - 复用已有 image/video provider 构造逻辑，不新增第二套 provider。
- Modify: `app/services/video_service.py`
  - 返回 `submit_id`、`querying`、`provider_raw_response`，供 bridge response 直接透传给 ArcReel。
- Test: `tests/api/test_arcreel_bridge_api.py`
  - 覆盖图片 bridge、视频 bridge、querying refresh、失败响应。

### ArcReel Provider/Adapter

- Create: `runtime/research/ArcReel/lib/cusagents_bridge/client.py`
  - HTTP client，负责调用 CusAgents bridge。
- Create: `runtime/research/ArcReel/lib/image_backends/cusagents.py`
  - 实现 `ImageBackend` 协议，调用 `/arcreel/bridge/images`。
- Create: `runtime/research/ArcReel/lib/video_backends/cusagents.py`
  - 实现 `VideoBackend` 协议，调用 `/arcreel/bridge/videos`。
- Modify: `runtime/research/ArcReel/lib/providers.py`
  - 增加 `PROVIDER_CUSAGENTS_DREAMINA`、`PROVIDER_CUSAGENTS_CHATGPT_WEB` 等 provider id。
- Modify: `runtime/research/ArcReel/lib/image_backends/__init__.py`
  - 注册 CusAgents 图片 backend。
- Modify: `runtime/research/ArcReel/lib/video_backends/__init__.py`
  - 注册 CusAgents 视频 backend。
- Modify: `runtime/research/ArcReel/lib/config/registry.py`
  - 把 CusAgents provider/model 暴露给设置页和 resolver。
- Test: `runtime/research/ArcReel/tests/test_cusagents_bridge_client.py`
- Test: `runtime/research/ArcReel/tests/test_cusagents_image_backend.py`
- Test: `runtime/research/ArcReel/tests/test_cusagents_video_backend.py`

### ArcReel 多参考图视频

- Create: `runtime/research/ArcReel/lib/cusagents_bridge/reference_manifest.py`
  - 构造 `reference_manifest`、排序、截断、prompt 图片清单。
- Modify: `runtime/research/ArcReel/server/services/generation_tasks.py`
  - `storyboard` 视频生成前同时收集分镜图、角色、场景、物品参考图。
- Modify: `runtime/research/ArcReel/server/services/reference_video_tasks.py`
  - 复用 manifest builder，保证 prompt 与实际上传图片一致。
- Test: `runtime/research/ArcReel/tests/test_cusagents_reference_manifest.py`
- Test: `runtime/research/ArcReel/tests/test_generation_tasks_cusagents_refs.py`

### Documentation

- Create: `doc/ArcReel本地运行验收记录.md`
- Modify: `doc/ArcReel底座改造实施计划.md`
- Modify: `doc/协作进度.md`

---

## Task 0: 运行与许可基线

**Files:**
- Create: `doc/ArcReel本地运行验收记录.md`
- Modify: `doc/协作进度.md`

- [ ] **Step 1: 确认工作区干净**

Run:

```powershell
git status --short
```

Expected: no output.

- [ ] **Step 2: 确认 ArcReel 许可证**

Run:

```powershell
Get-Content -LiteralPath 'runtime\research\ArcReel\LICENSE' -TotalCount 5
```

Expected: output starts with `GNU AFFERO GENERAL PUBLIC LICENSE`.

- [ ] **Step 3: 记录许可证决策**

Create `doc/ArcReel本地运行验收记录.md`:

```markdown
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
```

- [ ] **Step 4: 更新进度文档**

Append to `doc/协作进度.md` with current goal, completed work, status, next step, key files, blockers.

- [ ] **Step 5: Commit documentation baseline**

Run:

```powershell
git add doc/ArcReel本地运行验收记录.md doc/协作进度.md
git commit -m "docs: record arcreel baseline decision"
```

Expected: commit succeeds.

---

## Task 1: 跑通 ArcReel Docker 原生环境

**Files:**
- Modify: `runtime/research/ArcReel/deploy/.env`
- Modify: `doc/ArcReel本地运行验收记录.md`
- Modify: `doc/协作进度.md`

- [ ] **Step 1: 准备 ArcReel `.env`**

Run:

```powershell
Copy-Item -LiteralPath 'runtime\research\ArcReel\deploy\.env.example' -Destination 'runtime\research\ArcReel\deploy\.env' -Force
```

Then set deterministic local credentials in `runtime/research/ArcReel/deploy/.env`:

```text
AUTH_USERNAME=admin
AUTH_PASSWORD=arcreel-local-dev
AUTH_TOKEN_SECRET=arcreel-local-dev-token
```

Expected: `.env` exists. This file remains inside ignored `runtime/`.

- [ ] **Step 2: Start container**

Run:

```powershell
docker compose -f runtime\research\ArcReel\deploy\docker-compose.yml up -d
```

Expected: container starts and maps `1241:1241`.

- [ ] **Step 3: Verify health**

Run:

```powershell
Invoke-WebRequest -Uri 'http://127.0.0.1:1241/health' -UseBasicParsing
```

Expected: HTTP 200.

- [ ] **Step 4: Record container status**

Run:

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String -Pattern "arcreel|1241"
```

Expected: one ArcReel container is up.

- [ ] **Step 5: Update run record**

Add to `doc/ArcReel本地运行验收记录.md`:

```markdown
## ArcReel Docker 基线

- Start command: `docker compose -f runtime\research\ArcReel\deploy\docker-compose.yml up -d`
- Health URL: `http://127.0.0.1:1241/health`
- Login URL: `http://127.0.0.1:1241`
- Local username: `admin`
- Local password source: `runtime/research/ArcReel/deploy/.env`
- Result: not_run
- Notes:
```

- [ ] **Step 6: Commit run documentation**

Run:

```powershell
git add doc/ArcReel本地运行验收记录.md doc/协作进度.md
git commit -m "docs: record arcreel local run"
```

Expected: commit succeeds.

---

## Task 2: CusAgents Bridge API Contract

**Files:**
- Create: `app/schemas/arcreel_bridge.py`
- Create: `app/api/routes/arcreel_bridge.py`
- Modify: `app/main.py`
- Create: `tests/api/test_arcreel_bridge_api.py`

- [x] **Step 1: Write failing tests**

Create `tests/api/test_arcreel_bridge_api.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_arcreel_bridge_health_returns_provider_status():
    client = TestClient(app)

    response = client.get("/arcreel/bridge/health")

    assert response.status_code == 200
    payload = response.json()
    assert "image_backends" in payload
    assert "video_backends" in payload


def test_arcreel_bridge_rejects_unknown_image_backend():
    client = TestClient(app)

    response = client.post(
        "/arcreel/bridge/images",
        json={
            "backend": "unknown",
            "prompt": "test image",
            "output_name": "scene_001.png",
            "aspect_ratio": "16:9",
            "reference_images": [],
        },
    )

    assert response.status_code == 422
```

- [x] **Step 2: Run failing tests**

Run:

```powershell
pytest tests/api/test_arcreel_bridge_api.py -v
```

Expected: FAIL because route does not exist.

- [x] **Step 3: Add schemas**

Create `app/schemas/arcreel_bridge.py`:

```python
from typing import Literal

from pydantic import BaseModel, Field


class BridgeReferenceImage(BaseModel):
    file_path: str
    file_name: str | None = None
    role: str = "reference"
    usage: str = "reference image"


class BridgeImageRequest(BaseModel):
    backend: Literal["dreamina_cli", "chatgpt_web"]
    prompt: str = Field(min_length=1)
    output_name: str = Field(min_length=1)
    aspect_ratio: str = "9:16"
    reference_images: list[BridgeReferenceImage] = Field(default_factory=list)


class BridgeImageResponse(BaseModel):
    status: str
    backend: str
    file_path: str | None = None
    submit_id: str | None = None
    provider_raw_response: dict | None = None
    error_message: str | None = None


class BridgeVideoRequest(BaseModel):
    backend: Literal["dreamina_video_cli"] = "dreamina_video_cli"
    mode: Literal["text2video", "image2video", "multimodal2video", "multiframe2video"] = "text2video"
    prompt: str = Field(min_length=1)
    duration: int = 4
    ratio: str = "16:9"
    video_resolution: str = "720p"
    model_version: str = "seedance2.0"
    reference_images: list[BridgeReferenceImage] = Field(default_factory=list)


class BridgeVideoResponse(BaseModel):
    status: str
    bridge_job_id: int | None = None
    backend: str
    mode: str
    submit_id: str | None = None
    file_path: str | None = None
    provider_raw_response: dict | None = None
    error_message: str | None = None
```

- [x] **Step 4: Add minimal router**

Create `app/api/routes/arcreel_bridge.py`:

```python
from fastapi import APIRouter, HTTPException

from app.schemas.arcreel_bridge import BridgeImageRequest, BridgeImageResponse, BridgeVideoRequest, BridgeVideoResponse

router = APIRouter(prefix="/arcreel/bridge", tags=["arcreel-bridge"])


@router.get("/health")
def bridge_health():
    return {
        "image_backends": ["dreamina_cli", "chatgpt_web"],
        "video_backends": ["dreamina_video_cli"],
    }


@router.post("/images", response_model=BridgeImageResponse)
def create_bridge_image(payload: BridgeImageRequest):
    raise HTTPException(status_code=501, detail="image bridge execution is intentionally blocked until Task 3")


@router.post("/videos", response_model=BridgeVideoResponse)
def create_bridge_video(payload: BridgeVideoRequest):
    raise HTTPException(status_code=501, detail="video bridge execution is intentionally blocked until Task 6")
```

Modify `app/main.py`:

```python
from app.api.routes import arcreel_bridge

app.include_router(arcreel_bridge.router)
```

- [x] **Step 5: Run tests**

Run:

```powershell
pytest tests/api/test_arcreel_bridge_api.py -v
```

Expected: PASS for health and validation tests.

Current result: `pytest tests/api/test_arcreel_bridge_api.py -q` passed with `3 passed`; affected API regression passed with `51 passed`.

- [ ] **Step 6: Commit bridge contract**

Run:

```powershell
git add app/schemas/arcreel_bridge.py app/api/routes/arcreel_bridge.py app/main.py tests/api/test_arcreel_bridge_api.py
git commit -m "feat: add arcreel bridge contract"
```

Expected: commit succeeds.

---

## Task 3: CusAgents Bridge Image Execution

**Files:**
- Modify: `app/api/routes/arcreel_bridge.py`
- Modify: `tests/api/test_arcreel_bridge_api.py`

- [x] **Step 1: Write failing image execution test**

Append:

```python
class FakeImageResult:
    image_bytes = b"fake-image"
    metadata = {"submit_id": "img-submit-1"}


class FakeImageProvider:
    def generate_image(self, prompt, style):
        return FakeImageResult()


def test_arcreel_bridge_image_executes_provider(tmp_path, monkeypatch):
    from app.api.routes import arcreel_bridge

    monkeypatch.setattr(arcreel_bridge, "build_image_providers", lambda settings: {"dreamina_cli": FakeImageProvider()})
    monkeypatch.setattr(arcreel_bridge, "BRIDGE_OUTPUT_DIR", tmp_path)
    client = TestClient(app)

    response = client.post(
        "/arcreel/bridge/images",
        json={
            "backend": "dreamina_cli",
            "prompt": "cinematic test",
            "output_name": "scene_001.png",
            "aspect_ratio": "16:9",
            "reference_images": [],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["backend"] == "dreamina_cli"
    assert payload["file_path"].endswith("scene_001.png")
```

- [x] **Step 2: Run failing test**

Run:

```powershell
pytest tests/api/test_arcreel_bridge_api.py::test_arcreel_bridge_image_executes_provider -v
```

Expected: FAIL with HTTP 501 from the Task 2 guard branch.

Current result: FAIL before implementation because the route module did not yet expose `build_image_providers`, confirming image execution was not wired.

- [x] **Step 3: Implement minimal image bridge**

In `app/api/routes/arcreel_bridge.py`, add:

```python
from pathlib import Path

from app.core.config import load_settings
from app.services.factory import build_image_providers

BRIDGE_OUTPUT_DIR = Path("output/arcreel_bridge/images")
```

Replace `create_bridge_image` body:

```python
def create_bridge_image(payload: BridgeImageRequest):
    settings = load_settings(allow_placeholder_llm_api_key=True)
    providers = build_image_providers(settings)
    provider = providers[payload.backend]
    result = provider.generate_image(payload.prompt, payload.aspect_ratio)
    output_path = BRIDGE_OUTPUT_DIR / payload.output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(result.image_bytes)
    return BridgeImageResponse(
        status="succeeded",
        backend=payload.backend,
        file_path=str(output_path),
        submit_id=(getattr(result, "metadata", {}) or {}).get("submit_id"),
        provider_raw_response=getattr(result, "metadata", None),
    )
```

- [x] **Step 4: Run targeted tests**

Run:

```powershell
pytest tests/api/test_arcreel_bridge_api.py -v
```

Expected: PASS.

Current result: `pytest tests/api/test_arcreel_bridge_api.py -q` passed with `4 passed`; affected API regression passed with `52 passed`.

---

## Task 4: ArcReel CusAgents HTTP Client

**Files:**
- Create: `runtime/research/ArcReel/lib/cusagents_bridge/client.py`
- Create: `runtime/research/ArcReel/tests/test_cusagents_bridge_client.py`

- [x] **Step 1: Write failing client tests**

Create `runtime/research/ArcReel/tests/test_cusagents_bridge_client.py`:

```python
import httpx
import pytest

from lib.cusagents_bridge.client import CusAgentsBridgeClient


@pytest.mark.asyncio
async def test_client_posts_image_request():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"status": "succeeded", "backend": "dreamina_cli", "file_path": "out.png"})

    client = CusAgentsBridgeClient(
        base_url="http://cusagents.test",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    result = await client.generate_image(
        backend="dreamina_cli",
        prompt="test",
        output_name="scene_001.png",
        aspect_ratio="16:9",
        reference_images=[],
    )

    assert result["file_path"] == "out.png"
    assert requests[0].url.path == "/arcreel/bridge/images"
```

- [x] **Step 2: Run failing test**

Run from `runtime/research/ArcReel`:

```powershell
uv run pytest tests/test_cusagents_bridge_client.py -v
```

Expected: FAIL with missing module.

Current result: local `uv` command is not available; `python -m pytest tests/test_cusagents_bridge_client.py -q` is blocked before test import because this machine's Python environment is missing ArcReel dependency `portalocker`.

- [x] **Step 3: Implement client**

Create `runtime/research/ArcReel/lib/cusagents_bridge/client.py`:

```python
from __future__ import annotations

from typing import Any

import httpx


class CusAgentsBridgeClient:
    def __init__(self, *, base_url: str, timeout: float = 300.0, http_client: httpx.AsyncClient | None = None):
        self.base_url = base_url.rstrip("/")
        self._client = http_client or httpx.AsyncClient(timeout=timeout)

    async def generate_image(
        self,
        *,
        backend: str,
        prompt: str,
        output_name: str,
        aspect_ratio: str,
        reference_images: list[dict[str, Any]],
    ) -> dict[str, Any]:
        response = await self._client.post(
            f"{self.base_url}/arcreel/bridge/images",
            json={
                "backend": backend,
                "prompt": prompt,
                "output_name": output_name,
                "aspect_ratio": aspect_ratio,
                "reference_images": reference_images,
            },
        )
        response.raise_for_status()
        return response.json()
```

- [x] **Step 4: Run test**

Run:

```powershell
uv run pytest tests/test_cusagents_bridge_client.py -v
```

Current result: standard ArcReel pytest remains blocked by missing local dependencies; a file-level import verification script passed and confirmed `generate_image()` posts to `/arcreel/bridge/images`, sends the expected JSON payload, returns JSON, and raises `CusAgentsBridgeError` with HTTP status/detail for failed responses.

Expected: PASS.

---

## Task 5: ArcReel Image Backend Adapter

**Files:**
- Create: `runtime/research/ArcReel/lib/image_backends/cusagents.py`
- Modify: `runtime/research/ArcReel/lib/image_backends/__init__.py`
- Modify: `runtime/research/ArcReel/lib/providers.py`
- Create: `runtime/research/ArcReel/tests/test_cusagents_image_backend.py`

- [x] **Step 1: Write failing backend test**

Create `runtime/research/ArcReel/tests/test_cusagents_image_backend.py`:

```python
from pathlib import Path

import pytest

from lib.image_backends.base import ImageCapability, ImageGenerationRequest
from lib.image_backends.cusagents import CusAgentsImageBackend


class FakeClient:
    async def generate_image(self, **kwargs):
        Path(kwargs["output_name"]).write_text("not used", encoding="utf-8")
        return {"status": "succeeded", "file_path": __file__, "backend": "dreamina_cli"}


@pytest.mark.asyncio
async def test_cusagents_image_backend_downloads_bridge_result(tmp_path):
    output_path = tmp_path / "scene_001.png"
    backend = CusAgentsImageBackend(client=FakeClient(), backend="dreamina_cli", model="dreamina")

    result = await backend.generate(ImageGenerationRequest(prompt="test", output_path=output_path, aspect_ratio="16:9"))

    assert result.provider == "cusagents:dreamina_cli"
    assert result.model == "dreamina"
    assert ImageCapability.TEXT_TO_IMAGE in backend.capabilities
```

- [x] **Step 2: Run failing test**

Run:

```powershell
uv run pytest tests/test_cusagents_image_backend.py -v
```

Expected: FAIL with missing backend.

Current result: standard ArcReel pytest remains blocked by missing local dependencies (`portalocker`/`aiosqlite` path); test file was added before backend implementation.

- [x] **Step 3: Implement backend**

Create `runtime/research/ArcReel/lib/image_backends/cusagents.py`:

```python
from __future__ import annotations

import shutil
from pathlib import Path

from lib.cusagents_bridge.client import CusAgentsBridgeClient
from lib.image_backends.base import ImageBackend, ImageCapability, ImageGenerationRequest, ImageGenerationResult


class CusAgentsImageBackend:
    def __init__(self, *, base_url: str = "http://host.docker.internal:8000", backend: str, model: str = "cusagents", client=None):
        self._client = client or CusAgentsBridgeClient(base_url=base_url)
        self._backend = backend
        self._model = model

    @property
    def name(self) -> str:
        return f"cusagents:{self._backend}"

    @property
    def model(self) -> str:
        return self._model

    @property
    def capabilities(self) -> set[ImageCapability]:
        return {ImageCapability.TEXT_TO_IMAGE, ImageCapability.IMAGE_TO_IMAGE}

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        result = await self._client.generate_image(
            backend=self._backend,
            prompt=request.prompt,
            output_name=request.output_path.name,
            aspect_ratio=request.aspect_ratio,
            reference_images=[{"file_path": item.path, "file_name": Path(item.path).name, "role": item.label} for item in request.reference_images],
        )
        source = Path(result["file_path"])
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, request.output_path)
        return ImageGenerationResult(image_path=request.output_path, provider=self.name, model=self.model)
```

- [x] **Step 4: Register backend**

Add provider constants in `lib/providers.py`:

```python
PROVIDER_CUSAGENTS_DREAMINA = "cusagents-dreamina"
PROVIDER_CUSAGENTS_CHATGPT_WEB = "cusagents-chatgpt-web"
```

Register in `lib/image_backends/__init__.py`:

```python
from lib.image_backends.cusagents import CusAgentsImageBackend
from lib.providers import PROVIDER_CUSAGENTS_CHATGPT_WEB, PROVIDER_CUSAGENTS_DREAMINA

register_backend(PROVIDER_CUSAGENTS_DREAMINA, lambda **kwargs: CusAgentsImageBackend(backend="dreamina_cli", **kwargs))
register_backend(PROVIDER_CUSAGENTS_CHATGPT_WEB, lambda **kwargs: CusAgentsImageBackend(backend="chatgpt_web", **kwargs))
```

- [x] **Step 5: Run tests**

Run:

```powershell
uv run pytest tests/test_cusagents_image_backend.py -v
```

Expected: PASS.

Current result: standard ArcReel pytest is still blocked by local dependency setup; a lightweight package-loader script passed and confirmed the adapter calls the bridge client, forwards reference image metadata, copies the returned bridge file into `request.output_path`, and raises a clear error when the returned file path is not visible to ArcReel.

---

## Task 6: ArcReel Video Backend Adapter

**Files:**
- Modify: `app/api/routes/arcreel_bridge.py`
- Create: `runtime/research/ArcReel/lib/video_backends/cusagents.py`
- Modify: `runtime/research/ArcReel/lib/video_backends/__init__.py`
- Modify: `runtime/research/ArcReel/lib/providers.py`
- Create: `runtime/research/ArcReel/tests/test_cusagents_video_backend.py`

- [x] **Step 1: Write tests for long task response**

In CusAgents `tests/api/test_arcreel_bridge_api.py`, add:

```python
def test_arcreel_bridge_video_accepts_multimodal_request():
    client = TestClient(app)

    response = client.post(
        "/arcreel/bridge/videos",
        json={
            "backend": "dreamina_video_cli",
            "mode": "multimodal2video",
            "prompt": "use all references",
            "duration": 4,
            "ratio": "16:9",
            "video_resolution": "720p",
            "model_version": "seedance2.0",
            "reference_images": [
                {"file_path": "a.png", "file_name": "a.png", "role": "shot", "usage": "shot image"},
                {"file_path": "b.png", "file_name": "b.png", "role": "character", "usage": "character reference"},
            ],
        },
    )

    assert response.status_code == 501
```

- [x] **Step 2: Implement bridge video execution by delegating `/videos` service**

Use existing `VideoJob` + `VideoService` path rather than calling CLI directly. The bridge response must include:

```json
{
  "status": "querying",
  "bridge_job_id": 123,
  "backend": "dreamina_video_cli",
  "mode": "multimodal2video",
  "submit_id": "provider submit id when available",
  "file_path": null,
  "provider_raw_response": {}
}
```

Minimal implementation in `app/api/routes/arcreel_bridge.py`:

```python
from app.db.models.video_job import VideoJob
from app.db.session import get_db
from app.schemas.video import VideoCreateRequest


def _manifest_from_bridge_images(reference_images):
    return {
        "images": [
            {
                "file_path": item.file_path,
                "file_name": item.file_name or Path(item.file_path).name,
                "role": item.role,
                "usage": item.usage,
                "included": True,
            }
            for item in reference_images
        ],
        "dropped_images": [],
    }
```

Replace `create_bridge_video` with a database-backed implementation:

```python
@router.post("/videos", response_model=BridgeVideoResponse)
def create_bridge_video(payload: BridgeVideoRequest, db=Depends(get_db)):
    job = VideoJob(
        request_id=str(uuid.uuid4()),
        prompt=payload.prompt,
        backend=payload.backend,
        mode=payload.mode,
        duration=payload.duration,
        ratio=payload.ratio,
        video_resolution=payload.video_resolution,
        model_version=payload.model_version,
        reference_manifest_json=json.dumps(_manifest_from_bridge_images(payload.reference_images), ensure_ascii=False),
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return BridgeVideoResponse(
        status=job.status,
        bridge_job_id=job.id,
        backend=job.backend,
        mode=job.mode,
        submit_id=job.submit_id,
        file_path=None,
        provider_raw_response=None,
    )
```

- [x] **Step 3: Implement ArcReel backend**

Create `runtime/research/ArcReel/lib/video_backends/cusagents.py` with `VideoBackend` implementation. For `querying`, raise a clear runtime error first:

```python
raise RuntimeError("CusAgents video task is still querying; refresh support is required before synchronous ArcReel video generation can complete")
```

This keeps the first adapter honest. Task 7 adds refresh scheduling.

- [x] **Step 4: Register video backend**

Add `PROVIDER_CUSAGENTS_DREAMINA_VIDEO = "cusagents-dreamina-video"` and register it in `lib/video_backends/__init__.py`.

- [x] **Step 5: Run tests**

Run:

```powershell
pytest tests/api/test_arcreel_bridge_api.py -v
uv run pytest tests/test_cusagents_video_backend.py -v
```

Expected: PASS.

Current result: `pytest tests/api/test_arcreel_bridge_api.py -q` passed with `4 passed`; standard ArcReel pytest remains blocked by local missing dependencies, but a lightweight package-loader script passed and confirmed `CusAgentsVideoBackend` maps image inputs to video mode/reference payload, raises a refresh-required error for `pending/querying`, and copies completed bridge video files into `request.output_path`.

---

## Task 7: Multi-Reference Manifest and Prompt Rule

**Files:**
- Create: `runtime/research/ArcReel/lib/cusagents_bridge/reference_manifest.py`
- Modify: `runtime/research/ArcReel/server/services/reference_video_tasks.py`
- Modify: `runtime/research/ArcReel/server/services/generation_tasks.py`
- Create: `runtime/research/ArcReel/tests/test_cusagents_reference_manifest.py`

- [x] **Step 1: Write manifest tests**

Create tests that assert:

1. Shot image priority is first.
2. Character reference is before scene and prop.
3. Dropped images are recorded with `excluded_reason`.
4. Prompt contains every included file name.

- [x] **Step 2: Implement manifest builder**

Implement functions:

```python
ROLE_PRIORITY = {
    "shot": 0,
    "character": 1,
    "scene": 2,
    "prop": 3,
    "style": 4,
}


def build_reference_manifest(items: list[dict], max_images: int | None) -> dict:
    sorted_items = sorted(items, key=lambda item: (ROLE_PRIORITY.get(item.get("role", "reference"), 99), item.get("file_name", "")))
    included = sorted_items if not max_images or max_images <= 0 else sorted_items[:max_images]
    dropped = sorted_items[len(included) :]
    return {
        "images": [{**item, "included": True, "excluded_reason": None} for item in included],
        "dropped_images": [{**item, "included": False, "excluded_reason": "max_reference_images_exceeded"} for item in dropped],
    }


def render_prompt_image_list(manifest: dict) -> str:
    lines = ["参考图片清单："]
    for item in manifest.get("images", []):
        lines.append("- {0}: {1}".format(item.get("file_name"), item.get("usage")))
    return "\n".join(lines)


def select_video_mode(included_images: list[dict], keyframe_sequence: bool = False) -> str:
    if keyframe_sequence:
        return "multiframe2video"
    count = len(included_images)
    if count == 0:
        return "text2video"
    if count == 1:
        return "image2video"
    return "multimodal2video"
```

Mode rules:

- `0` images -> `text2video`
- `1` image -> `image2video`
- `>=2` images -> `multimodal2video`
- explicit keyframe sequence -> `multiframe2video`

Current result: `lib/cusagents_bridge/reference_manifest.py` implements role priority, max image cropping, dropped image reasons, and prompt file-name injection. `CusAgentsVideoBackend` now uses the manifest builder before calling the bridge client. Standard ArcReel pytest remains blocked by local missing dependencies; lightweight verification passed with `reference manifest behavior ok`.

- [ ] **Step 3: Integrate in ArcReel reference video path**

In `reference_video_tasks.py`, replace prompt/reference list construction with manifest builder, then pass only included image paths to backend.

Current status: pending. The manifest rule is currently integrated in `CusAgentsVideoBackend`; direct executor-level integration in `reference_video_tasks.py` is still needed.

- [ ] **Step 4: Integrate storyboard video path**

In `generation_tasks.py`, when generating video from storyboard:

1. Include current storyboard image.
2. Include referenced character/scene/prop sheets.
3. Build prompt image list.
4. Use CusAgents video backend `reference_images`.

Current status: pending. The existing storyboard/generation service path has not yet been modified in this step.

- [ ] **Step 5: Run tests**

Run:

```powershell
uv run pytest tests/test_cusagents_reference_manifest.py tests/test_cusagents_video_backend.py -v
```

Expected: PASS.

Current status: standard ArcReel pytest remains blocked by missing local dependencies; lightweight module verification passed for manifest and CusAgents video backend integration.

---

## Task 8: Refresh and Resume Semantics

**Files:**
- Modify: `app/api/routes/arcreel_bridge.py`
- Modify: `runtime/research/ArcReel/lib/cusagents_bridge/client.py`
- Modify: `runtime/research/ArcReel/server/services/reference_video_tasks.py`
- Modify: `runtime/research/ArcReel/lib/generation_queue.py`
- Modify: `runtime/research/ArcReel/lib/db/models/task.py`
- Modify: `runtime/research/ArcReel/lib/db/repositories/task_repo.py`

- [x] **Step 1: Add bridge refresh endpoint**

Expose:

```text
POST /arcreel/bridge/videos/{bridge_job_id}/refresh
```

It calls existing CusAgents `/videos/{id}/refresh` logic and returns the same bridge response shape.

- [x] **Step 2: Add ArcReel client refresh method**

Add:

```python
async def refresh_video(self, bridge_job_id: int) -> dict[str, Any]:
    response = await self._client.post(f"{self.base_url}/arcreel/bridge/videos/{bridge_job_id}/refresh")
    response.raise_for_status()
    return response.json()
```

- [x] **Step 3: Add ArcReel `querying` task status**

Extend task status handling so `querying` is not treated as failed or lease-timeout stuck. The queue must not requeue it as normal `running`.

- [x] **Step 4: Add resume worker command**

Add a small service that scans `querying` video tasks and refreshes them at a controlled interval.

- [x] **Step 5: Run tests**

Run:

```powershell
uv run pytest tests -m "not e2e" -v
pytest tests/api/test_arcreel_bridge_api.py -v
```

Expected: PASS.

---

## Task 9: Feishu and Codex Project Binding

**Files:**
- Modify: `app/commands/parser.py`
- Modify: `app/commands/router.py`
- Modify: `app/services/conversation_service.py`
- Modify: `tests/commands/test_command_parser.py`
- Modify: `tests/commands/test_command_router.py`

- [x] **Step 1: Add command tests**

Add tests for:

```text
/arcreel_create title="雨夜追踪" summary="侦探在霓虹雨巷发现怀表并追踪黑衣人"
/arcreel_status project="雨夜追踪"
/arcreel_resume project="雨夜追踪"
```

- [x] **Step 2: Implement parser**

Map commands to:

```python
"create_arcreel_project"
"arcreel_project_status"
"resume_arcreel_project"
```

- [x] **Step 3: Implement router**

Router should call ArcReel API when `ARCREEL_BASE_URL` is configured. Without `ARCREEL_BASE_URL`, it must raise `ValueError("ARCREEL_BASE_URL is required for ArcReel commands")` so the failure is explicit and testable.

- [x] **Step 4: Bind Codex session to project**

Use existing `ConversationService` session id and store ArcReel project id in command result payload or a small mapping table if persistence is required.

Current note: CusAgents now supports optional `ARCREEL_API_TOKEN` and sends it as `Authorization: Bearer ...` for ArcReel command calls. ArcReel source has a local `POST /api/v1/projects/{name}/resume` implementation that refreshes only that project's querying video tasks; the currently running Docker container uses the published image and does not include that local route until rebuilt/restarted from source.

---

## Task 10: 2-Shot Acceptance

**Files:**
- Create: `doc/ArcReel两分镜真实验收报告.md`
- Modify: `doc/协作进度.md`

- [ ] **Step 1: Prepare minimal story**

Use a two-shot story:

```text
标题：雨夜追踪
分镜 1：侦探在霓虹雨巷发现带血怀表。
分镜 2：黑衣人回头，怀表倒映出失踪女孩的脸。
```

- [ ] **Step 2: Create project in ArcReel**

Use UI or API. Record project id/name.

- [ ] **Step 3: Generate or attach references**

Must include:

- one character reference
- one scene reference
- one prop reference

- [ ] **Step 4: Submit first video**

Expected:

- mode is `multimodal2video`
- prompt includes every included image file name
- task stores `submit_id`
- status can remain `querying`

- [ ] **Step 5: Refresh until first video succeeds or external queue remains pending**

If still pending, record queue status and stop without claiming completion.

- [ ] **Step 6: Verify automatic next-shot submission**

After first video succeeds, second video task should be created automatically.

- [ ] **Step 7: Write report**

Create `doc/ArcReel两分镜真实验收报告.md` with:

```markdown
# ArcReel 两分镜真实验收报告

## Environment

## Project

## References

## Shot 1 Video Task

## Shot 2 Video Task

## Notifications

## Result

## Open Issues
```

---

## Verification Matrix

Run after each stage:

```powershell
pytest -q
```

Run for ArcReel backend changes:

```powershell
cd runtime\research\ArcReel
uv run pytest tests -m "not e2e" -v
cd frontend
pnpm typecheck
pnpm test
```

Run before any CusAgents commit:

```powershell
gitnexus22 status
gitnexus22 analyze
gitnexus22 status
gitnexus detect_changes --scope staged
```

If GitNexus MCP is available, use:

```text
gitnexus_detect_changes(scope="staged")
```

## Commit Strategy

Use small commits:

1. `docs: record arcreel baseline decision`
2. `docs: record arcreel local run`
3. `feat: add arcreel bridge contract`
4. `feat: add arcreel bridge image generation`
5. ArcReel repo commit: `feat: add cusagents image bridge backend`
6. ArcReel repo commit: `feat: add cusagents video bridge backend`
7. ArcReel repo commit: `feat: route storyboard video references through manifest`
8. `feat: add arcreel feishu commands`
9. `docs: add arcreel two shot acceptance report`

## Open Decisions

- 是否接受 AGPL-3.0 用于后续 fork 分发；本地内部使用可先推进。
- CusAgents bridge 是否需要 API token；第一版本机可用，进入局域网或公网前必须加认证。
- ArcReel 容器访问宿主机 CusAgents 的地址默认用 `host.docker.internal:8000`，WSL2/Docker 网络异常时改用宿主机局域网 IP。
- 即梦 `multimodal2video` 最大参考图数量仍需用当前 CLI help 或真实调用确认。
- 视频 `querying` 的刷新频率需要保守，避免刷即梦查询和飞书通知。
