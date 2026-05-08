# 即梦 CLI 集成功能与使用说明

更新时间：2026-05-08

## 1. 当前集成状态

即梦 CLI 已安装并完成 OAuth 登录验证，可供本机 agent、脚本和 CusAgents 工作流调用。

已验证信息：

- CLI 路径：`C:\Users\91799\bin\dreamina.exe`
- 用户 PATH：已包含 `C:\Users\91799\bin`
- CLI 版本：`c58a6a2-dirty`
- 构建时间：`2026-05-07T09:52:59Z`
- 登录状态：已登录
- 账号等级：`maestro`
- 当前额度：`14844`
- Codex skill：`C:\Users\91799\.codex\skills\dreamina-cli\SKILL.md`
- Agents skill：`C:\Users\91799\.agents\skills\dreamina-cli\SKILL.md`

如果新终端里还不能直接运行 `dreamina`，先用完整路径：

```powershell
C:\Users\91799\bin\dreamina.exe --help
```

## 2. 可用功能

即梦 CLI 当前提供以下核心能力：

- `text2image`：文生图
- `text2video`：文生视频
- `image2image`：图生图，支持 1 到 10 张本地参考图
- `image2video`：单图生视频
- `frames2video`：首尾帧生视频
- `multiframe2video`：多图连贯故事视频
- `multimodal2video`：全能参考视频生成，支持图片、视频、音频等参考
- `image_upscale`：图片超清放大
- `query_result`：查询异步任务结果
- `list_task`：查看历史任务
- `user_credit`：查询账号额度
- `session`：管理即梦 CLI 会话
- `login` / `relogin` / `logout`：管理登录状态

所有真实生成任务都会消耗即梦额度。执行生成前应先确认需求、模型、分辨率和任务数量。

## 3. 常用检查命令

查看总帮助：

```powershell
C:\Users\91799\bin\dreamina.exe --help
```

查看版本：

```powershell
C:\Users\91799\bin\dreamina.exe version
```

查看额度：

```powershell
C:\Users\91799\bin\dreamina.exe user_credit
```

查看历史任务：

```powershell
C:\Users\91799\bin\dreamina.exe list_task
```

查询异步任务：

```powershell
C:\Users\91799\bin\dreamina.exe query_result --submit_id=<submit_id>
```

## 4. 文生图用法

查看参数：

```powershell
C:\Users\91799\bin\dreamina.exe text2image --help
```

示例：

```powershell
C:\Users\91799\bin\dreamina.exe text2image --prompt="a clean product render of a red cube on white background" --ratio=1:1 --resolution_type=2k --poll=30
```

常见参数：

- `--prompt`：生成提示词
- `--ratio`：支持 `21:9`、`16:9`、`3:2`、`4:3`、`1:1`、`3:4`、`2:3`、`9:16`
- `--resolution_type`：按模型支持 `1k`、`2k`、`4k`
- `--model_version`：支持 `3.0`、`3.1`、`4.0`、`4.1`、`4.5`、`4.6`、`5.0`
- `--poll`：提交后等待结果的秒数，超时后可用 `query_result` 继续查

## 5. 文生视频用法

查看参数：

```powershell
C:\Users\91799\bin\dreamina.exe text2video --help
```

示例：

```powershell
C:\Users\91799\bin\dreamina.exe text2video --prompt="a cinematic slow push-in shot of a futuristic city at sunrise" --duration=5 --ratio=16:9 --poll=60
```

常见参数：

- `--prompt`：生成提示词
- `--duration`：视频时长，当前支持 4 到 15 秒
- `--ratio`：支持 `1:1`、`3:4`、`16:9`、`4:3`、`9:16`、`21:9`
- `--video_resolution`：一般为 `720p`，`seedance2.0_vip` 支持 `1080p`
- `--model_version`：支持 `seedance2.0`、`seedance2.0fast`、`seedance2.0_vip`、`seedance2.0fast_vip`
- `--poll`：提交后等待结果的秒数

CLI 原生命令默认模型是 `seedance2.0fast`。CusAgents 的视频后端会显式传入项目默认值 `seedance2.0`，避免被 CLI 默认值带偏；如果后续要优先速度，可在命令或环境变量中显式改为 `seedance2.0fast`。

## 6. 图生图用法

查看参数：

```powershell
C:\Users\91799\bin\dreamina.exe image2image --help
```

示例：

```powershell
C:\Users\91799\bin\dreamina.exe image2image --images .\input.png --prompt="turn this into a clean watercolor illustration" --ratio=1:1 --resolution_type=2k --poll=30
```

说明：

- `--images`：本地图片路径，一次最多 10 张
- `--prompt`：编辑或重绘提示词
- `--ratio`：支持常见横竖屏比例
- `--resolution_type`：支持 `2k`、`4k`
- `--model_version`：支持 `4.0`、`4.1`、`4.5`、`4.6`、`5.0`

## 7. 图生视频用法

查看参数：

```powershell
C:\Users\91799\bin\dreamina.exe image2video --help
```

示例：

```powershell
C:\Users\91799\bin\dreamina.exe image2video --image=.\first.png --prompt="camera slowly pushes in, soft light, subtle motion" --duration=5 --poll=60
```

说明：

- `--image`：本地首帧图片路径
- `--prompt`：视频运动和风格描述
- `--duration`：按模型支持 3 到 15 秒不等
- `--video_resolution`：一般为 `720p`，`seedance2.0_vip` 支持 `1080p`
- `--model_version`：支持 `3.0`、`3.0fast`、`3.0pro`、`3.5pro`、`seedance2.0`、`seedance2.0fast`、`seedance2.0_vip`、`seedance2.0fast_vip`

如果有多张图片并希望形成连贯故事，优先使用 `multiframe2video`，不要把多图任务硬塞给 `image2video`。

## 8. 异步任务处理规则

多数生成命令是异步任务。提交成功后应记录返回中的：

- `submit_id`
- `gen_status`
- 命令参数
- 输出文件或结果 URL

判断提交成功不要只看进程退出码。应以 CLI 返回内容为准：

- 有 `submit_id`
- `gen_status` 为 `querying` 或 `success`

如果 `gen_status` 是 `fail`，需要读取 `fail_reason` 后再决定是否重试。

查询任务：

```powershell
C:\Users\91799\bin\dreamina.exe query_result --submit_id=<submit_id>
```

查看历史：

```powershell
C:\Users\91799\bin\dreamina.exe list_task
```

## 9. 登录和重新登录

当前已经登录成功。正常情况下不需要重新登录。

如果登录态失效：

```powershell
C:\Users\91799\bin\dreamina.exe login --headless
```

CLI 会输出：

- `verification_uri`
- `user_code`
- `device_code`
- `expires_at`

在浏览器打开 `verification_uri` 完成授权后，用：

```powershell
C:\Users\91799\bin\dreamina.exe login checklogin --device_code=<device_code> --poll=30
```

强制重新登录：

```powershell
C:\Users\91799\bin\dreamina.exe relogin
```

退出登录：

```powershell
C:\Users\91799\bin\dreamina.exe logout
```

## 10. 在 CusAgents 工作流中的建议接入方式

当前文档只记录“本机 CLI 已可用”。如果要把即梦接成 CusAgents 的正式图片或视频 provider，建议按现有 provider 架构做最小增量：

1. 新增 `dreamina_cli` 后端名称。
2. 新增 provider，内部通过 `subprocess` 调用 `C:\Users\91799\bin\dreamina.exe`。
3. 每次提交任务时记录命令、参数、`submit_id`、状态和结果。
4. 生成任务先用 `--poll` 短轮询，未完成时把任务保存为可查询状态。
5. 用 `query_result` 做后续异步结果回收。
6. 在前端或飞书命令层显式提示“即梦任务会消耗额度”。

推荐的后端边界：

- 文生图：映射到 `text2image`
- 图生图：映射到 `image2image`
- 文生视频：独立视频任务，不混入当前图片 provider
- 图生视频：独立视频任务，不混入当前图片 provider
- 查询：用 `submit_id` 作为外部任务 ID

如果只需要临时使用，不必先改项目代码，可以让 agent 直接调用 CLI 完成生成，再把产物路径写回 `output/`。

## 11. 方案一：通过即梦生图

### 11.1 目标定位

即梦生图应作为 CusAgents 的正式图片后端接入，后端名称建议为：

```text
dreamina_cli
```

它和现有 `comfyui_remote`、`third_party`、`codex_cli`、`chatgpt_web` 属于同一类能力：都服务于当前工作流里的 `image_backend`。

推荐首版只接：

- `text2image`：文生图

第二版再扩：

- `image2image`：图生图
- `image_upscale`：图片超清

首版不要把视频能力混入图片 provider。即梦视频应走独立视频任务链路，见下一节。

### 11.2 用户侧入口

API 入口保持现有 `POST /jobs` 不变，只新增 backend 值：

```json
{
  "topic": "赛博武侠雨夜决战",
  "style_preset": "cinematic",
  "target_shot_count": 3,
  "image_backend": "dreamina_cli"
}
```

飞书工作流入口：

```text
/create topic="赛博武侠雨夜决战" style=cinematic shots=3 backend=dreamina_cli
```

手机轻控制页：

```text
出图后端下拉框新增 dreamina_cli
```

### 11.3 系统运行流程

完整流程如下：

```text
用户 /create 或 POST /jobs
-> Job 入库，image_backend=dreamina_cli
-> Worker 执行 OrchestrationService
-> outline 生成故事大纲
-> storyboard 生成分镜
-> prompt service 生成每个镜头的正向/负向 prompt
-> ImageGenerationService 选择 DreaminaCliImageProvider
-> DreaminaCliImageProvider 组装即梦 text2image 参数
-> DreaminaCliClient 调用 dreamina.exe text2image
-> 解析 CLI stdout/stderr，提取 submit_id、gen_status、结果文件或结果 URL
-> 如果 poll 内完成，读取本地图片 bytes
-> 写入 Asset，workflow_json 记录 submit_id、命令参数、模型、比例、额度相关信息
-> QualityService 校验素材数量和状态
-> Job 进入 waiting_review
-> 飞书/手机端查看图片
```

### 11.4 推荐配置项

新增配置建议：

```text
DREAMINA_CLI_PATH=C:\Users\91799\bin\dreamina.exe
DREAMINA_IMAGE_MODEL_VERSION=5.0
DREAMINA_IMAGE_RATIO=16:9
DREAMINA_IMAGE_RESOLUTION_TYPE=2k
DREAMINA_IMAGE_POLL_SECONDS=120
DREAMINA_IMAGE_TIMEOUT_SECONDS=180
DREAMINA_IMAGE_OUTPUT_DIR=./output/dreamina/images
DREAMINA_IMAGE_RETRY_ATTEMPTS=0
```

推荐默认值：

- `DREAMINA_IMAGE_MODEL_VERSION=5.0`
- `DREAMINA_IMAGE_RATIO` 默认从工作流风格推导，推导失败用 `16:9`
- `DREAMINA_IMAGE_RESOLUTION_TYPE=2k`
- `DREAMINA_IMAGE_POLL_SECONDS=120`
- `DREAMINA_IMAGE_RETRY_ATTEMPTS=0`

即梦任务会消耗额度，默认不自动重试，避免失败时重复扣费。

### 11.5 Provider 边界

建议新增文件：

```text
app/providers/image/dreamina_cli_client.py
app/providers/image/dreamina_cli_provider.py
tests/providers/test_dreamina_cli_provider.py
```

`DreaminaCliClient` 负责：

- 构造 `dreamina.exe text2image` 命令
- 执行 subprocess
- 设置 timeout
- 解析 CLI 输出
- 识别 `submit_id`
- 判断 `gen_status`
- 查找或下载生成图片
- 在必要时调用 `query_result`

`DreaminaCliImageProvider` 负责：

- 将当前 storyboard prompt 归一化为即梦文生图 prompt
- 合并 negative prompt
- 映射比例、分辨率、模型版本
- 返回 `ImageGenerationResult`

### 11.6 输出和记录

图片文件建议落地到：

```text
output/dreamina/images/
```

`Asset.workflow_json` 建议记录：

```json
{
  "provider_name": "dreamina_cli",
  "submit_id": "...",
  "gen_status": "success",
  "command": ["dreamina.exe", "text2image", "..."],
  "model_version": "5.0",
  "ratio": "16:9",
  "resolution_type": "2k",
  "poll_seconds": 120,
  "stdout": "...",
  "stderr": "..."
}
```

### 11.7 错误处理

失败分类建议：

- `not_logged_in`：CLI 登录失效，提示运行 `dreamina login --headless`
- `insufficient_credit`：额度不足，提示先查 `user_credit`
- `compliance_required`：遇到 `AigcComplianceConfirmationRequired`，提示去 Dreamina Web 确认授权
- `timeout`：poll 超时但已有 `submit_id`，保留 `submit_id` 供后续查询
- `generation_failed`：`gen_status=fail`，记录 `fail_reason`
- `output_missing`：成功但找不到输出文件或结果 URL

对于 poll 超时，首版推荐把当前 asset 标为 `failed`，但在 `workflow_json` 中保留 `submit_id`。后续可再做异步回收任务。

### 11.8 五阶段落地计划

第一阶段：CLI Client 与解析层

- 新增 `DreaminaCliClient`
- 支持 `text2image`
- 支持 `--poll`
- 支持 timeout
- 支持解析 `submit_id`、`gen_status`、输出路径或 URL
- 单元测试用 fake runner，不消耗真实额度

第二阶段：图片 Provider 接入

- 新增 `DreaminaCliImageProvider`
- 注册到 `build_image_providers()`
- `JobCreateRequest.image_backend` 增加 `dreamina_cli`
- `/mobile/jobs` 下拉框增加 `dreamina_cli`
- `RuntimeHealthService` 增加 CLI 路径、登录态和额度检查

第三阶段：工作流闭环

- 用 `POST /jobs image_backend=dreamina_cli` 创建任务
- 直跑 `run_configured_job(job_id)`
- 验证 Job 到达 `waiting_review`
- 验证 Asset 文件存在
- 验证 `workflow_json.provider_name=dreamina_cli`

第四阶段：飞书和手机端验收

- 飞书 `/create ... backend=dreamina_cli`
- 等待 worker 消费
- 飞书回传首张图
- 手机页可看到后端和素材预览

第五阶段：文档、风控和可恢复性

- README 和当前系统详细使用说明同步新增 backend
- 进度文档记录真实验收 job_id、asset_id、输出路径
- `.env.example` 补全 `DREAMINA_IMAGE_*`
- 明确“即梦会消耗额度”
- 明确超时后用 `query_result --submit_id=...` 恢复查询

第五阶段完成后，即梦生图才算从“CLI 可用”升级为“CusAgents 正式图片后端可用”。

## 12. 方案二：通过即梦生成视频

### 12.1 目标定位

即梦视频不应混入当前 `image_backend`。推荐新增独立视频任务体系，后端名称建议：

```text
dreamina_video_cli
```

首版只接：

- `text2video`：文生视频

第二版再扩：

- `image2video`：单图生视频
- `frames2video`：首尾帧生视频
- `multiframe2video`：多图连贯故事视频
- `multimodal2video`：多模态参考视频生成

原因：视频任务的时长、分辨率、异步等待、输出文件、审核方式和成本模型都与图片不同。把它塞进 `ImageGenerationService` 会让当前图片工作流变复杂。

### 12.2 用户侧入口

推荐新增 API：

```text
POST /videos
GET  /videos/{video_id}
GET  /videos/{video_id}/assets
POST /videos/{video_id}/retry
POST /videos/{video_id}/cancel
```

请求示例：

```json
{
  "topic": "未来城市日出，镜头缓慢推进",
  "prompt": "a cinematic slow push-in shot of a futuristic city at sunrise",
  "duration": 5,
  "ratio": "16:9",
  "video_resolution": "720p",
  "model_version": "seedance2.0",
  "backend": "dreamina_video_cli"
}
```

飞书命令建议：

```text
/video prompt="a cinematic slow push-in shot of a futuristic city at sunrise" duration=5 ratio=16:9 model=seedance2.0
```

更偏工作流的入口：

```text
/video_create topic="赛博武侠雨夜追逐" style=cinematic duration=5 ratio=16:9
```

首版推荐先做 `/video prompt="..."`，不要一开始就自动从故事生成完整视频。这样能快速验证即梦视频链路。

### 12.3 系统运行流程

文生视频首版流程：

```text
用户 /video 或 POST /videos
-> VideoJob 入库
-> VideoJobDispatcher 入队
-> Worker 执行 run_configured_video_job(video_id)
-> DreaminaCliVideoProvider 组装 text2video 参数
-> DreaminaCliClient 调用 dreamina.exe text2video
-> 解析 submit_id、gen_status、结果文件或 URL
-> 如果 poll 内完成，保存 mp4 到 output/dreamina/videos/
-> VideoJob 状态改为 completed 或 waiting_review
-> 记录 VideoAsset
-> 飞书回发视频文件路径或上传视频消息
```

图生视频第二版流程：

```text
已有图片 Asset 或用户上传图片
-> 创建 VideoJob，mode=image2video
-> DreaminaCliVideoProvider 调用 image2video --image=<path>
-> 保存视频结果
```

首尾帧第三版流程：

```text
已有首帧/尾帧图片
-> 创建 VideoJob，mode=frames2video
-> 调用 frames2video
-> 保存视频结果
```

### 12.4 推荐数据模型

新增模型建议：

```text
VideoJob
VideoAsset
```

`VideoJob` 字段建议：

```text
id
request_id
topic
prompt
backend
mode
status
current_step
duration
ratio
video_resolution
model_version
submit_id
notification_target_id
error_message
created_at
updated_at
```

`VideoAsset` 字段建议：

```text
id
video_job_id
file_path
preview_path
thumbnail_path
duration
ratio
video_resolution
status
metadata_json
created_at
```

首版可以不做复杂视频分镜表。等 `text2video` 链路稳定后，再扩展 `VideoStoryboard` 或 `VideoShot`。

### 12.5 推荐配置项

```text
DREAMINA_VIDEO_MODEL_VERSION=seedance2.0
DREAMINA_VIDEO_RATIO=16:9
DREAMINA_VIDEO_DURATION=5
DREAMINA_VIDEO_RESOLUTION=720p
DREAMINA_VIDEO_POLL_SECONDS=180
DREAMINA_VIDEO_TIMEOUT_SECONDS=300
DREAMINA_VIDEO_OUTPUT_DIR=./output/dreamina/videos
DREAMINA_VIDEO_RETRY_ATTEMPTS=0
```

推荐默认值：

- `DREAMINA_VIDEO_MODEL_VERSION=seedance2.0`
- `DREAMINA_VIDEO_DURATION=5`
- `DREAMINA_VIDEO_RATIO=16:9`
- `DREAMINA_VIDEO_RESOLUTION=720p`
- `DREAMINA_VIDEO_RETRY_ATTEMPTS=0`

视频更消耗额度且通常是长任务，首版不建议自动重试。`querying` 不是失败状态，应保留 `submit_id`，后续通过 `POST /videos/{video_id}/refresh` 或 `query_result` 恢复查询。

### 12.6 Provider 边界

建议新增文件：

```text
app/providers/video/base.py
app/providers/video/dreamina_cli_video_client.py
app/providers/video/dreamina_cli_video_provider.py
app/services/video_service.py
app/workers/video_jobs.py
app/api/routes/videos.py
tests/providers/test_dreamina_cli_video_provider.py
tests/services/test_video_service.py
tests/api/test_videos_api.py
```

`DreaminaCliVideoProvider` 负责：

- `text2video`
- 以后扩展 `image2video`
- 以后扩展 `frames2video`
- 返回统一 `VideoGenerationResult`

`VideoService` 负责：

- 保存视频文件
- 保存 `VideoAsset`
- 更新 `VideoJob`
- 通知飞书或返回状态

### 12.7 输出和记录

视频文件建议落地：

```text
output/dreamina/videos/
```

`VideoAsset.metadata_json` 建议记录：

```json
{
  "provider_name": "dreamina_video_cli",
  "mode": "text2video",
  "submit_id": "...",
  "gen_status": "success",
  "command": ["dreamina.exe", "text2video", "..."],
  "model_version": "seedance2.0",
  "duration": 5,
  "ratio": "16:9",
  "video_resolution": "720p",
  "poll_seconds": 180,
  "stdout": "...",
  "stderr": "..."
}
```

### 12.8 错误处理

视频失败分类建议：

- `not_logged_in`
- `insufficient_credit`
- `compliance_required`
- `timeout`
- `generation_failed`
- `output_missing`
- `unsupported_duration`
- `unsupported_ratio`
- `unsupported_model`

如果 `text2video` poll 超时，或 CLI 返回 `gen_status=querying` 且带有 `submit_id`，应将 `VideoJob` 状态置为：

```text
querying
```

然后允许：

```text
POST /videos/{video_id}/refresh
```

内部调用：

```powershell
dreamina.exe query_result --submit_id=<submit_id> --download_dir=./output/dreamina/videos
```

### 12.9 五阶段落地计划

第一阶段：最小视频 CLI Client

- 新增 `DreaminaCliVideoClient`
- 支持 `text2video`
- fake runner 单元测试
- 能解析 `submit_id`、`gen_status`、结果路径或 URL

第二阶段：视频数据模型和 API

- 新增 `VideoJob`
- 新增 `VideoAsset`
- 新增 Alembic 迁移
- 新增 `POST /videos`
- 新增 `GET /videos/{id}`

第三阶段：Worker 和真实文生视频闭环

- 新增 `run_configured_video_job(video_id)`
- 新增 `VideoService`
- 真实执行一条 `text2video`
- 结果保存到 `output/dreamina/videos/`

第四阶段：飞书命令和回执

- 新增 `/video prompt="..."` 命令
- 支持 `duration`、`ratio`、`model`
- 执行完成后回发状态、文件路径或视频消息
- 失败时回发 `submit_id` 和 `fail_reason`

第五阶段：视频工作流扩展和使用文档

- 文档补齐视频任务运行步骤
- `.env.example` 补齐 `DREAMINA_VIDEO_*`
- 补 `query_result` 恢复流程
- 增加 `image2video` 的预留接口说明
- 明确视频任务消耗额度更高，默认不自动重试

第五阶段完成后，即梦视频才算从“手工 CLI 可用”升级为“CusAgents 独立视频生成能力可用”。

## 13. 两个方案的推荐实施顺序

推荐顺序：

1. 先做即梦生图 `dreamina_cli`
2. 再做即梦文生视频 `dreamina_video_cli`
3. 最后再扩图生视频、多帧视频和多模态视频

原因：

- 生图可以复用现有 `Job`、`Asset`、`ImageGenerationService`、飞书图片回传、手机预览和质量检查。
- 视频需要新增数据模型、API、Worker、资产类型和通知方式，改动面更大。
- 先把 `DreaminaCliClient` 的命令执行、输出解析、登录失效、额度不足、合规确认等问题在生图链路里打磨稳定，再复用到视频链路，风险最低。

最小可交付顺序：

```text
阶段 1：DreaminaCliClient 通用执行与解析
阶段 2：dreamina_cli 图片后端
阶段 3：真实 /create backend=dreamina_cli 验收
阶段 4：dreamina_video_cli 文生视频任务
阶段 5：飞书命令、文档、恢复查询和额度风控
```

## 14. Agent 使用规范

后续 agent 使用即梦时应遵守：

- 先运行 `dreamina <subcommand> --help` 确认参数，不硬编码模型支持。
- 真实生成前明确告知会消耗额度。
- 优先小批量提交，避免一次性消耗大量额度。
- 对异步任务保存 `submit_id`，不要丢失查询入口。
- 如遇 `AigcComplianceConfirmationRequired`，需要先到 Dreamina Web 完成一次授权确认。
- 如遇登录失效，按本文“登录和重新登录”流程恢复。

## 15. 本次集成进度

已完成：

- 读取飞书《即梦 CLI 体验指南》。
- 执行官方安装脚本。
- 安装 `dreamina.exe` 到 `C:\Users\91799\bin`。
- 将 `C:\Users\91799\bin` 加入用户 PATH。
- 下载并安装 `dreamina-cli` skill。
- 完成 OAuth 设备登录。
- 使用 `user_credit` 验证登录态和额度。
- 将功能、进度和使用说明写入 `E:\AIProject\CusAgents\doc`。

未做：

- 尚未把 `dreamina_cli` 注册为 CusAgents 正式 provider。
- 尚未执行真实图片或视频生成任务。
- 尚未为即梦任务做数据库模型、队列任务或飞书命令映射。

建议下一步：

- 如果目标是“手动让 agent 用即梦生成素材”，当前已足够。
- 如果目标是“通过 `/create backend=dreamina_cli` 自动接入工作流”，需要新增 provider、配置、测试和文档。
## 16. CusAgents 集成完成状态

本轮已把即梦从“本机 CLI 可用”推进到 CusAgents 正式集成：

1. 图片后端：`dreamina_cli`
   - 已接入 `POST /jobs`
   - 已接入移动端 backend 下拉
   - 已接入 provider 工厂和运行期健康检查
   - 已支持失败、超时、`querying` 时保留 `submit_id`

2. 视频后端：`dreamina_video_cli`
   - 已新增独立 `VideoJob` / `VideoAsset`
   - 已新增 `POST /videos`、`GET /videos/{id}`、`GET /videos/{id}/assets`、`POST /videos/{id}/retry`、`POST /videos/{id}/cancel`、`POST /videos/{id}/refresh`
   - 已新增 worker 执行入口 `run_configured_video_job`
   - 已新增飞书命令 `/video` 和 `/video_status`

3. 恢复查询：
   - 图片失败 Asset 的 `workflow_json` 会保留 `submit_id` 和 `gen_status`
   - 视频任务可通过 `POST /videos/{video_id}/refresh` 调用 `query_result`
   - 视频任务如果仍返回 `querying`，继续保持 `querying`，不按短任务失败处理
   - 视频任务如果恢复查询返回 `success` 和本地视频路径，会写入 `VideoAsset`，重复刷新不会重复插入同一 `submit_id` 的已完成资产
   - 也可手动执行：

```powershell
C:\Users\91799\bin\dreamina.exe query_result --submit_id=<submit_id> --download_dir=./output/dreamina/videos
```

4. 额度风控：
   - `RuntimeHealthService` 会检查 `dreamina_cli` 路径和 `user_credit`
   - `.env.example` 已明确图片/视频均默认 `*_RETRY_ATTEMPTS=0`
   - 真实验收前先执行 `user_credit`

当前尚未在本轮执行真实生成；如需真实验收，推荐只跑一张图片和一个 4 秒 720p 视频样本。
