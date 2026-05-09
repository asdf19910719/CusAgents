# ArcReel 完整故事到视频流程使用说明

本文说明如何从一个故事概要开始，走到分镜剧本、人物/场景/道具参考图、分镜视频生成和最终剧本回填。

## 当前能力边界

当前项目已经打通：

1. ArcReel 项目、剧本、分镜和素材目录管理。
2. ArcReel 通过 CusAgents bridge 请求图片和视频生成。
3. CusAgents 通过 Dreamina CLI 执行真实视频生成。
4. 视频 `querying` 后由 RQ worker + scheduler 后台自动轮询。
5. 视频完成后，ArcReel `resume` 可把生成结果写回项目剧本。

当前还不是单个按钮全自动完成所有创作步骤。最稳的真实流程是：先用故事概要生成或整理结构化剧本和参考图需求，再逐项生成参考图、提交视频，最后由后台轮询和 `resume` 收尾。

## 启动服务

完整流程至少需要四个服务在线：

1. Redis
2. CusAgents API
3. CusAgents RQ worker
4. CusAgents RQ scheduler
5. ArcReel 本地源码服务

### CusAgents API

```powershell
$env:QUEUE_NAME='arcreel-acceptance'
$env:AUTO_ENQUEUE_JOBS='true'
$env:ARCREEL_PROJECTS_HOST_ROOT='E:\AIProject\CusAgents\runtime\research\ArcReel\deploy\projects'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

### RQ Worker

```powershell
$env:QUEUE_NAME='arcreel-acceptance'
$env:AUTO_ENQUEUE_JOBS='true'
$env:ARCREEL_PROJECTS_HOST_ROOT='E:\AIProject\CusAgents\runtime\research\ArcReel\deploy\projects'
python scripts/run_worker.py
```

### RQ Scheduler

```powershell
$env:QUEUE_NAME='arcreel-acceptance'
$env:AUTO_ENQUEUE_JOBS='true'
python scripts/run_scheduler.py
```

`worker` 负责真正执行任务，`scheduler` 负责把到期的延迟轮询任务投递回队列。视频长任务如果停在 `querying`，必须同时保持这两个进程在线。

### ArcReel

当前本地源码验证实例：

```text
http://127.0.0.1:1242
```

ArcReel 容器内访问宿主机 CusAgents bridge 时，推荐配置：

```text
http://host.docker.internal:8010
```

宿主机直接访问 CusAgents API 时使用：

```text
http://127.0.0.1:8010
```

## 推荐输入

给自动执行流程时，最少提供：

```text
故事概要：一句到一段均可
```

如果不补充其他信息，默认按以下参数执行：

1. 分镜数量：2 到 4 个，优先保持短流程。
2. 单镜时长：4 秒。
3. 画幅：16:9。
4. 视频模型：`seedance2.0`。
5. 视频后端：`cusagents-dreamina-video` / `dreamina_video_cli`。
6. 参考图：需要真实生成时会消耗图片额度；也可先用占位图验证视频流程。

更完整的输入可以包括：

```text
标题：
故事概要：
风格：
分镜数量：
主要角色：
主要场景：
关键道具：
是否真实生成参考图：
是否真实生成视频：
```

## 实际执行流程

### 1. 根据概要整理项目设定

把故事概要整理为：

1. 项目标题
2. 风格提示词
3. 角色列表
4. 场景列表
5. 道具列表
6. 分镜列表

分镜应包含：

1. `segment_id` 或 `shot_index`
2. 分镜标题
3. 剧情动作
4. 画面描述
5. 运镜
6. 角色引用
7. 场景引用
8. 道具引用
9. 时长

### 2. 创建 ArcReel 项目

通过 ArcReel UI 或 API 创建项目，并记录项目名。

项目配置需要使用 CusAgents bridge 后端：

```text
image backend: cusagents
video backend: cusagents-dreamina-video/seedance2.0
bridge base_url: http://host.docker.internal:8010
```

### 3. 写入分镜剧本

在 ArcReel 项目中保存 `scripts/episode_1.json`。

剧本里的每个分镜都应先有空的生成资产字段，例如：

```json
{
  "generated_assets": {
    "storyboard_image": "storyboards/scene_S1.png",
    "storyboard_last_image": null,
    "video_clip": null,
    "video_uri": null,
    "video_thumbnail": null
  }
}
```

### 4. 生成或上传参考图

参考图通常包括：

1. 人物参考图：`characters/角色名.png`
2. 场景参考图：`scenes/场景名.png`
3. 道具参考图：`props/道具名.png`
4. 分镜图：`storyboards/scene_S1.png`

如果真实生成参考图，会调用图片后端并消耗额度。若只是验证视频链路，可以先使用人工上传图或占位图。

### 5. 提交分镜视频

ArcReel 视频后端会把当前分镜图、角色图、场景图、道具图组合成 CusAgents bridge 请求。

CusAgents 会创建 `VideoJob`，并根据参考图数量选择模式：

1. 无参考图：`text2video`
2. 1 张参考图：`image2video`
3. 2 张及以上参考图：`multimodal2video`
4. 关键帧序列：`multiframe2video`

视频提交后可能返回：

```text
pending
querying
completed
failed
```

`querying` 表示已经提交到 Dreamina，正在外部队列中等待或生成，不代表失败。

### 6. 后台自动轮询

当视频仍为 `querying` 时，CusAgents 会安排后台 poll。

后台轮询依赖：

1. `python scripts/run_worker.py`
2. `python scripts/run_scheduler.py`

不要在 `querying` 状态下重复提交同一个视频任务，否则可能重复消耗额度。

### 7. 调用 ArcReel resume 回填剧本

`resume` 的含义是“让 ArcReel 从当前项目状态继续推进一次”。

它主要做这些事：

1. 扫描该项目里仍处于 `querying` 或已成功但未回填的 CusAgents 视频任务。
2. 调用 CusAgents bridge refresh 查询视频是否已完成。
3. 如果视频已完成，把生成的 mp4 镜像到 ArcReel 项目目录，例如：

```text
videos/scene_S1.mp4
```

4. 把这个相对路径写回剧本：

```json
"video_clip": "videos/scene_S1.mp4"
```

5. 如果当前分镜完成，再继续推进后续待生成分镜。

也就是说，`resume` 不是重新生成故事，也不是重新提交已完成任务；它是根据现有任务状态做“恢复查询、补偿回填、继续下一步”。

调用示例：

```powershell
$login = Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:1242/api/v1/auth/token `
  -ContentType 'application/x-www-form-urlencoded' `
  -Body 'username=admin&password=arcreel-local-dev'

$headers = @{ Authorization = "Bearer $($login.access_token)" }

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:1242/api/v1/projects/<project-name>/resume `
  -Headers $headers
```

### 8. 验收结果

最终至少检查：

1. `scripts/episode_1.json` 中每个分镜都有 `generated_assets.video_clip`。
2. `videos/scene_S*.mp4` 文件存在且大小正常。
3. CusAgents `VideoJob` 为 `completed`。
4. 没有重复提交同一分镜的视频任务。

## 我可以代执行的内容

你给故事概要后，我可以自动执行：

1. 检查 API、ArcReel、Redis、worker、scheduler 是否在线。
2. 根据故事概要整理标题、角色、场景、道具和分镜结构。
3. 创建或准备 ArcReel 项目。
4. 写入 `episode_1.json`。
5. 生成或准备参考图。
6. 提交分镜视频任务。
7. 查询并监控后台轮询状态。
8. 视频完成后调用 `resume` 回填剧本。
9. 输出最终验收报告。

执行前需要明确：

1. 是否允许真实生成参考图。
2. 是否允许真实生成视频。
3. 分镜数量和单镜时长。

真实生成图片和视频都会消耗外部额度；视频通常耗时较长，可能从几十分钟到更久。
