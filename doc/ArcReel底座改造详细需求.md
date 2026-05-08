# ArcReel 底座改造详细需求

更新时间：2026-05-08

## 1. 背景与选择

用户已选择方案 B：以本地克隆的 `runtime/research/ArcReel` 为主项目底座，在 ArcReel 已有影视工作台、项目资产、任务队列、费用追踪、FFmpeg 合成和剪映导出能力上，改造并接入 CusAgents 已实现的本地特殊能力。

本需求文档用于指导后续设计与实施，不直接进入编码。核心原则是：ArcReel 负责“影视项目产品形态和工作台”，CusAgents 负责“本地自动化能力和现有专用生成链路”，两者通过明确适配层集成，避免无边界地复制代码。

## 2. 总目标

建设一个可全程自动化的本地影视生成工作台：

1. 输入故事概要、故事大纲、世界观、角色设定、场景设定、物品设定等文本。
2. 由 AI 自动生成结构化分镜剧本。
3. 根据故事设定生成角色三视图、场景图、物品图和可选风格图。
4. 根据分镜剧本和参考资产生成分镜图，或生成多宫格分镜图后切分；该步骤可配置跳过。
5. 根据分镜剧本、分镜图、角色/场景/物品参考图生成视频片段。
6. 每个分镜视频生成完成后，系统自动继续生成下一个分镜视频。
7. 视频任务按长任务处理，保留 `submit_id`，支持 `querying`、恢复查询、自动通知和断点续跑。
8. 第一版以 ArcReel Web UI + 后端任务为主，不再重复开发无 UI 版本；后续继续增强质量门、合成、导出和人工干预能力。

## 3. 范围

### 3.1 必须纳入第一阶段的范围

- 以 ArcReel 作为主应用入口，保留其 Web UI、项目管理、资产预览、任务状态、视频合成和导出基础。
- 接入 CusAgents 的 `dreamina_cli` 图片生成能力。
- 接入 CusAgents 的 `dreamina_video_cli` 视频生成能力。
- 接入 ChatGPT Web 生图能力，作为可选图片 provider。
- 接入飞书命令入口和通知能力，用于发起任务、查询状态和接收完成/失败通知。
- 接入 Codex 正式会话能力，保证多轮执行时可保留上下文，而不是每次命令都丢失历史。
- 改造 ArcReel 视频生成规则，支持“分镜图 + 角色/场景/物品参考图”同时参与视频生成。
- 支持视频任务 `querying`、`submit_id`、恢复查询和服务重启后的继续调度。
- 支持视频完成后自动提交下一个分镜视频。

### 3.2 暂不纳入第一阶段的范围

- 不承诺一次性完成完整成片质量优化。
- 不优先实现复杂时间线剪辑器。
- 不优先实现多供应商成本最优调度。
- 不优先实现自动视觉一致性评分。
- 不优先实现商业化多租户权限体系。
- 不在 Windows 原生环境中强行运行 ArcReel Agent runtime。

## 4. 用户核心业务规则

### 4.1 参考图视频规则

只要当前分镜存在任意图片参考，就必须走带图视频生成：

- 有分镜图时，分镜图作为当前镜头构图、站位、动作起点或首帧参考。
- 有角色三视图或角色参考图时，必须上传给视频后端，并在 prompt 中说明角色名称和用途。
- 有场景图时，必须上传给视频后端，并在 prompt 中说明场景名称和用途。
- 有物品图时，必须上传给视频后端，并在 prompt 中说明物品名称和用途。
- 所有参与视频生成的图片都必须进入 `reference_manifest`。
- 最终视频 prompt 中必须列出每张图片的文件名、类型、业务名称和用途。

这里的“image2video”是业务含义上的“带图视频生成”，不是强制调用单图 `image2video` 命令。工程实现必须根据图片数量和模型能力路由到合适模式。

### 4.2 视频模式路由

默认视频模型为 `seedance2.0`。

推荐路由规则：

- `reference_images_count == 0`：使用 `text2video`。
- `reference_images_count == 1`：使用 `image2video`。
- `reference_images_count >= 2`：使用 `multimodal2video`。
- 存在明确首尾帧或多关键帧序列时：使用 `multiframe2video`。

如果上传图片数量超过即梦 CLI 或目标 provider 的上限，按以下优先级截断并记录：

- 当前分镜图。
- 当前分镜出场主角参考图。
- 当前场景参考图。
- 当前分镜关键物品参考图。
- 次要角色参考图。
- 风格参考图。

被截断的图片必须写入任务元数据，便于排查一致性问题。

### 4.3 视频长任务规则

视频生成通常可能需要几十分钟或数小时，系统不能假设几分钟内完成。

必须支持：

- 提交任务后立即保存 `submit_id`。
- `querying` 状态长期保留，不视为失败。
- 可通过 `submit_id` 恢复查询。
- Web UI、飞书和 API 均可查询长任务状态。
- 服务重启后可扫描并恢复未完成视频任务。
- 视频成功后保存视频资产并通知用户。
- 视频失败后保存失败原因并通知用户。
- 视频仍在 `querying` 时不频繁通知，避免刷屏。
- 单个分镜视频完成后自动调度下一个分镜视频。

## 5. 推荐总体架构

### 5.1 主体结构

推荐采用“ArcReel Fork 主仓库 + CusAgents 能力桥接”的架构。

ArcReel 侧负责：

- Web UI。
- 项目、分集、分镜、素材和任务展示。
- 资产目录与版本管理。
- 任务队列和进度追踪。
- 视频片段预览。
- FFmpeg 粗合成。
- 剪映导出。
- 后续人工调整入口。

CusAgents 侧负责：

- 即梦 CLI 图片生成。
- 即梦 CLI 视频生成。
- ChatGPT Web 生图。
- 飞书命令和通知。
- Codex 正式会话执行。
- 已实现的 `submit_id/querying/refresh` 长任务语义。
- 本地浏览器登录态、CLI 登录态、外部生成服务的适配。

中间新增 Bridge/Adapter 层：

- `cusagents_bridge`：ArcReel 调用 CusAgents 能力的统一适配层。
- `DreaminaImageProvider`：映射 ArcReel 图片生成请求到 `dreamina_cli`。
- `DreaminaVideoProvider`：映射 ArcReel 视频生成请求到 `dreamina_video_cli`。
- `ChatGptWebImageProvider`：映射 ArcReel 图片生成请求到 ChatGPT Web 自动化。
- `FeishuCommandBridge`：将飞书命令转为 ArcReel 项目操作或任务查询。
- `CodexSessionBridge`：将 ArcReel/飞书中的 AI 执行请求绑定到可恢复的 Codex 会话。

### 5.2 环境要求

推荐运行方式：

- ArcReel 主服务运行在 Docker 或 WSL2。
- CusAgents 可以作为 sidecar 服务运行在宿主机或独立 Python 环境。
- 即梦 CLI 和 ChatGPT Web 自动化优先运行在有真实登录态的宿主机侧。
- ArcReel 容器通过 HTTP API 或本机端口访问 CusAgents bridge。

不推荐方式：

- 不推荐直接在 Windows 原生环境运行 ArcReel Agent runtime。
- 不推荐在容器内强行复用宿主机浏览器登录态。
- 不推荐把所有 CusAgents 代码直接复制进 ArcReel 主仓库。

## 6. 核心功能需求

### 6.1 项目创建

用户可通过 ArcReel UI、API 或飞书命令创建故事视频项目。

输入字段：

- 项目标题。
- 故事概要或故事大纲。
- 世界观设定。
- 角色设定。
- 场景设定。
- 物品设定。
- 风格说明。
- 目标视频比例。
- 目标分镜数量。
- 单镜头默认时长。
- 图片 provider。
- 视频 provider。
- 视频模型版本，默认 `seedance2.0`。
- 是否生成分镜图。
- 是否生成多宫格图并切分。

输出结果：

- ArcReel 项目。
- 结构化项目配置。
- 初始任务队列。
- 可恢复的 pipeline run 记录。

### 6.2 AI 分镜剧本

系统根据输入故事自动生成结构化分镜剧本。

每个分镜至少包含：

- 分镜序号。
- 分镜标题。
- 剧情内容。
- 画面描述。
- 镜头语言。
- 角色出场列表。
- 场景引用。
- 物品引用。
- 情绪和动作。
- 时长。
- 画幅比例。
- 生成分镜图所需 prompt。
- 生成视频所需 prompt。
- 需要引用的参考资产名称。

分镜结果必须可编辑、可重生成、可部分锁定。

### 6.3 参考资产生成

系统根据故事设定生成资产库。

资产类型：

- 角色三视图。
- 角色表情或服装补充图。
- 场景图。
- 物品图。
- 风格参考图。

每个资产必须保存：

- 文件路径。
- 文件名。
- 资产类型。
- 业务名称。
- prompt。
- provider。
- submit_id 或外部任务 id。
- 生成状态。
- 版本信息。
- 是否锁定。
- 是否允许参与视频生成。

第一版优先保证每个关键角色、关键场景、关键物品至少有一张可用参考图。

### 6.4 分镜图生成

分镜图步骤可配置启用或跳过。

启用时支持：

- 每个分镜单独生成一张分镜图。
- 多宫格分镜图生成后自动切分。
- 从 ArcReel 原有 `storyboard`、`grid` 能力复用 UI 和资产结构。
- 使用角色、场景、物品参考图增强一致性。

跳过时：

- 视频生成仍使用角色、场景、物品参考图。
- 不因没有分镜图而退化为纯文本视频，除非没有任何参考图。

### 6.5 视频生成编排

系统按分镜顺序串行生成视频。

每个分镜视频提交前必须：

- 收集当前分镜图。
- 收集当前分镜关联角色图。
- 收集当前分镜关联场景图。
- 收集当前分镜关联物品图。
- 构造 `reference_manifest`。
- 生成带文件名和用途说明的 prompt。
- 根据图片数量选择 `text2video/image2video/multimodal2video/multiframe2video`。
- 保存任务参数和模型版本。

提交后：

- 保存 `submit_id`。
- 状态进入 `querying` 或等价长任务状态。
- 不阻塞用户请求。
- 后台轮询或手动 refresh 可恢复查询。
- 成功后写入视频资产。
- 自动推进下一个分镜。
- 全部分镜完成后进入项目完成或合成阶段。

### 6.6 自动通知

通知渠道第一版优先复用飞书。

必须通知：

- 项目创建成功。
- 分镜剧本生成完成。
- 参考资产生成失败。
- 分镜图生成失败。
- 单个视频生成成功。
- 单个视频生成失败。
- 项目全部视频生成完成。

不应频繁通知：

- 视频仍处于 `querying` 的普通轮询结果。
- 无状态变化的重复查询。

通知内容至少包含：

- 项目名称。
- 分镜序号。
- 当前状态。
- `submit_id`。
- 输出文件路径或资产链接。
- 失败原因。
- 恢复查询入口。

### 6.7 Codex 正式会话

系统需要保留 Codex 会话上下文，用于后续多轮执行和自动化修复。

需求：

- 每个项目可绑定一个或多个 Codex 会话。
- 飞书或 UI 发起的后续命令可复用已有会话。
- 会话需要记录 project id、session id、最近任务、执行状态和摘要。
- 不应每次命令都新建完全无上下文的一次性进程。
- 会话中断后可恢复或创建新会话并带入项目摘要。

### 6.8 ChatGPT Web 生图

ChatGPT Web 生图作为图片 provider 之一。

需求：

- 支持使用真实 Chrome 用户登录态。
- 支持打开 ChatGPT 网页、提交 prompt、等待生成、下载图片。
- 支持保存浏览器 profile 路径。
- 支持失败截图和错误日志。
- 支持 provider 健康检查。
- DOM 或页面流程变化时应优雅失败，不影响其他 provider。

该能力适合作为补充 provider，不作为第一版唯一依赖。

## 7. 与 ArcReel 的具体改造点

### 7.1 Provider 层

新增或改造：

- 图片 provider：`dreamina_cli`。
- 图片 provider：`chatgpt_web`。
- 视频 provider：`dreamina_video_cli`。
- Provider capability 中明确支持 `start_image`、`end_image`、`reference_images`、`max_reference_images`。
- Provider result 中保留 `submit_id`、`querying`、`provider_raw_response`。

### 7.2 视频工作流模式

ArcReel 原有模式需要合并增强：

- `storyboard`：分镜图继续作为视频首帧或构图参考。
- `grid`：宫格图切分后作为分镜图使用。
- `reference_video`：角色/场景/物品 sheet 作为视频参考图。
- 新增合并规则：当分镜图和参考资产同时存在时，必须同时传入视频 provider。

### 7.3 任务队列

ArcReel 原有任务队列需要扩展长任务语义：

- `queued`
- `running`
- `querying`
- `succeeded`
- `failed`
- `cancelled`
- `paused`
- `needs_review`

`querying` 不应被 lease 回收机制误判为卡死任务。需要单独的恢复查询调度器。

### 7.4 项目资产与 manifest

每个视频任务需要保存 `reference_manifest`。

Manifest 字段建议：

- `file_name`
- `file_path`
- `asset_type`
- `asset_name`
- `usage`
- `priority`
- `included`
- `excluded_reason`
- `provider_role`

视频 prompt 必须由 manifest 生成，避免上传图片和 prompt 描述不一致。

### 7.5 飞书与外部入口

新增飞书命令能力：

- 创建故事视频项目。
- 查询项目状态。
- 查询当前正在生成的分镜。
- 查询指定 `submit_id`。
- 暂停项目。
- 恢复项目。
- 重试失败分镜。
- 获取输出链接。

## 8. 数据需求

第一版可以优先复用 ArcReel 现有数据模型，但必须能表达以下概念：

- `StoryProject` 或 ArcReel project 扩展字段。
- `StoryShot` 或 ArcReel segment 扩展字段。
- `ReferenceAsset`。
- `ShotImage`。
- `ShotVideoTask`。
- `PipelineRun`。
- `GenerationProviderConfig`。
- `ReferenceManifest`。
- `CodexConversationSession`。
- `OutboundNotification`。

如果 ArcReel 已有等价表或文件结构，应优先扩展，不重复新增平行模型。只有在无法表达 CusAgents 特殊语义时再新增表。

## 9. API 需求

面向 UI 和飞书 bridge 的 API 至少包括：

- `POST /story-projects`：创建故事视频项目。
- `GET /story-projects/{id}`：查看项目详情。
- `POST /story-projects/{id}/plan`：生成或重生成分镜剧本。
- `POST /story-projects/{id}/references`：生成参考资产。
- `POST /story-projects/{id}/storyboards`：生成分镜图或宫格图。
- `POST /story-projects/{id}/videos/next`：提交下一个待生成分镜视频。
- `POST /story-projects/{id}/resume`：恢复项目流水线。
- `POST /video-tasks/{id}/refresh`：刷新单个视频任务。
- `GET /video-tasks/{id}`：查询单个视频任务。
- `POST /story-projects/{id}/pause`：暂停项目。
- `POST /story-projects/{id}/retry-failed`：重试失败任务。

如果直接在 ArcReel 原有 API 命名下实现，应保持语义一致，并在文档中给出映射。

## 10. UI 需求

第一版应优先复用 ArcReel UI。

必须展示：

- 项目列表。
- 项目当前阶段。
- 分镜列表。
- 每个分镜的剧本文本。
- 每个分镜关联参考图。
- 每个分镜图或宫格切分图。
- 每个视频任务状态。
- `submit_id`。
- 失败原因。
- 手动刷新按钮。
- 暂停、恢复、重试入口。
- 最终视频片段列表。

后续增强：

- 分镜剧本编辑器。
- 参考图替换和锁定。
- 图片优先级调整。
- 质量门和人工审核队列。
- 粗剪预览。
- 成本预估和实际费用对比。

## 11. 质量门需求

第一版只做硬校验：

- 必填输入存在。
- 分镜 JSON 可解析。
- 参考资产文件存在。
- 图片路径可访问。
- 视频任务保存了 `submit_id`。
- 视频完成后文件存在。
- `reference_manifest` 和 prompt 中的图片文件名一致。
- 失败任务有错误原因。

后续再做软质量判断：

- 角色一致性评分。
- 场景一致性评分。
- 道具一致性评分。
- 视频时长偏差检查。
- 图像空白或异常检测。
- 低质量结果自动重试。
- 超预算暂停。

## 12. 验收标准

### 12.1 最小真实验收

使用一个包含 2 个分镜的小故事进行验收。

验收必须通过：

- 能在 ArcReel UI 或 API 创建项目。
- 能生成结构化分镜剧本。
- 能生成至少 1 个角色参考图、1 个场景参考图、1 个物品参考图。
- 能生成或跳过分镜图。
- 第 1 个分镜视频提交时，如果有多张参考图，实际模式为 `multimodal2video`。
- 第 1 个分镜视频 prompt 包含所有上传图片的文件名和用途说明。
- 视频任务保存 `submit_id`。
- 视频处于 `querying` 时可关闭服务并恢复查询。
- 第 1 个视频成功后自动提交第 2 个分镜视频。
- 所有分镜视频完成后项目状态进入 completed 或 ready_for_composition。
- 飞书收到完成通知。

### 12.2 自动化测试验收

必须覆盖：

- provider 路由测试。
- reference manifest 构造测试。
- prompt 图片清单测试。
- 视频长任务 `querying` 测试。
- `submit_id` 恢复查询测试。
- 完成后自动推进下一分镜测试。
- 飞书通知测试。
- ChatGPT Web provider 失败降级测试。

### 12.3 环境验收

必须记录：

- ArcReel Docker/WSL2 启动方式。
- CusAgents bridge 启动方式。
- 即梦 CLI 登录态检查方式。
- ChatGPT Web 登录态检查方式。
- 飞书配置方式。
- Codex 会话配置方式。

## 13. 风险与约束

- ArcReel 是 AGPL-3.0，直接 fork 或分发改造版本需要接受 AGPL-3.0 约束；如未来商业闭源分发，必须重新评估许可证风险。
- ArcReel 依赖 Claude Agent SDK，Windows 原生环境不适合直接作为主运行环境。
- 即梦 CLI 和 ChatGPT Web 依赖本机登录态，容器化调用需要 bridge，不应强依赖容器内浏览器。
- ChatGPT Web DOM 和登录流程可能变化，应视为不稳定 provider。
- Dreamina 视频生成耗时由外部队列决定，不能承诺完成时间。
- ArcReel 现有任务队列和 CusAgents 当前 DB/worker 模型不完全一致，直接迁移代码成本较高。
- 多张参考图并不保证模型完全遵循，需要后续质量门和人工审核。
- `multimodal2video` 图片上限需要通过当前 CLI help 或真实调用确认。

## 14. 阶段拆分

### 阶段 0：许可与运行环境确认

- 确认 AGPL-3.0 接受范围。
- 确认 ArcReel 作为 fork 使用，还是仅内部本地使用。
- 确认 Docker/WSL2 运行路径。
- 确认 CusAgents bridge 是否独立服务。

### 阶段 1：跑通 ArcReel 本地环境

- 启动 ArcReel Docker/WSL2。
- 登录默认账号。
- 配置至少一个文本 provider。
- 跑通一个 ArcReel 原生项目。
- 记录本地启动文档。

### 阶段 2：接入即梦图片和视频 provider

- 接入 `dreamina_cli` 图片 provider。
- 接入 `dreamina_video_cli` 视频 provider。
- 支持 `seedance2.0` 默认模型。
- 支持 `submit_id` 和 `querying`。
- 支持 provider 健康检查。

### 阶段 3：改造多参考图视频规则

- 合并 `storyboard` 和 `reference_video` 思路。
- 实现 `reference_manifest`。
- 实现 prompt 图片文件名和用途注入。
- 实现模式路由。
- 实现图片超限截断与记录。

### 阶段 4：接入 ChatGPT Web 生图

- 配置真实 Chrome profile。
- 实现生成、下载、失败截图。
- 接入 provider 列表。
- 增加健康检查和失败降级。

### 阶段 5：接入飞书、Codex 会话和自动通知

- 飞书命令创建项目。
- 飞书查询状态。
- 视频完成/失败通知。
- Codex 会话绑定项目。
- 支持恢复会话继续执行。

### 阶段 6：真实 2 分镜验收

- 使用最小故事跑通完整链路。
- 记录 `submit_id`。
- 等待或恢复查询视频结果。
- 验证第 1 个视频完成后自动提交第 2 个。
- 生成验收报告。

### 阶段 7：UI、质量门、合成和导出增强

- 增强 UI 配置。
- 增加质量门。
- 增加粗剪合成。
- 增强剪映导出。
- 增加人工审核队列。

## 15. 工作量评估

在当前 CusAgents 已有第一版故事视频后端闭环的前提下，方案 B 的主要工作不是“从零实现能力”，而是“把能力迁移/桥接进 ArcReel 产品形态”。

粗略估计：

- 阶段 0-1：1 到 2 天。
- 阶段 2：2 到 4 天。
- 阶段 3：2 到 4 天。
- 阶段 4：1 到 3 天。
- 阶段 5：2 到 4 天。
- 阶段 6：1 到 2 天，但真实视频等待时间不可控。
- 阶段 7：按增强范围 1 到 3 周。

第一版可用版本预计 1.5 到 3 周。若要达到稳定产品化版本，预计 4 到 8 周。

## 16. 推荐结论

方案 B 可以提高“产品完整度”和“可视化工作台”落地效率，但它不应理解为简单把 ArcReel 克隆代码直接改几处即可完成。更稳妥的方式是：

1. 以 ArcReel 作为主应用底座。
2. 保留 ArcReel 的 UI、项目、资产、任务、合成和导出体系。
3. 通过 bridge 接入 CusAgents 已有的即梦、ChatGPT Web、飞书、Codex 会话和长任务能力。
4. 优先改造视频阶段的多参考图规则和长任务恢复。
5. 用 2 分镜真实验收验证方案，再扩大到完整故事项目。

后续进入实施前，应先产出单独的实施计划，明确 ArcReel 侧改哪些文件、CusAgents bridge 侧暴露哪些 API，以及数据如何迁移或映射。
