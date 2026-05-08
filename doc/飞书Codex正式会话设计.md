# 飞书 Codex 正式会话设计

## 目标

把当前“每条飞书普通文本或 `/codex` 都独立执行一次 `codex exec`”改造成“按 `chat_id` 维持连续上下文”的正式会话层，同时保持现有工作流命令 `/create`、`/status`、`/approve` 等不进入会话历史。

## 已确认约束

1. 会话按 `chat_id` 共享。
2. 空闲超时后自动切新会话，并保留手动重置。
3. 超长历史使用“旧消息摘要 + 最近消息原文”。
4. 只有普通文本和 `/codex` 进入会话。
5. `/create`、`/status`、`/retry`、`/approve`、`/cancel`、`/assets`、`/health` 不进入会话。

## 现状问题

当前 `run_codex` 链路会为每条命令新建一条 `CodexRun`，Worker 直接执行一次新的 `codex exec`。仓库上下文会保留，但聊天历史不会自动续接，因此：

1. 同一飞书会话里的连续提问不会自动继承前文。
2. 无法手动重置某个 chat 的上下文。
3. 无法在数据库层追踪“这次 Codex 执行属于哪条会话”。
4. 后续若要补权限、审计、记忆层，会缺少稳定的会话主键。

## 目标架构

在现有 `CommandRouter -> CodexRun -> Worker -> CodexRunService` 之间插入正式会话层：

1. `CommandRouter` 在处理普通文本或 `/codex` 时，先通过 `ConversationService` 命中或创建当前 `chat_id` 的活跃会话。
2. 当前用户消息先写入 `ConversationMessage`。
3. `ConversationService` 根据会话摘要和最近原文消息组装一份“本次执行快照 prompt”。
4. `CodexRun` 保存原始用户输入、绑定的 `session_id`、以及最终实际执行的 `resolved_prompt_text`。
5. Worker 执行完成后，把 assistant 输出写回同一会话。
6. 当消息数量超过阈值时，旧消息被压缩进一条 `summary` 消息，最近消息保持原样。

## 数据模型

### 1. `conversation_sessions`

表示一条按 `chat_id` 隔离的共享会话。

建议字段：

1. `id`
2. `chat_id`
3. `status`
   可选值：`active`、`expired`、`reset`
4. `started_at`
5. `last_message_at`
6. `closed_at`
7. `close_reason`
8. `created_at`
9. `updated_at`

说明：

1. 同一个 `chat_id` 同时只允许一条 `active` 会话。
2. 当空闲超时命中时，旧会话标记为 `expired`，新建一条 `active` 会话。
3. 当手动 `/new` 时，旧会话标记为 `reset`，再新建一条 `active` 会话。

### 2. `conversation_messages`

表示会话中的一条消息或摘要。

建议字段：

1. `id`
2. `session_id`
3. `role`
   可选值：`user`、`assistant`、`summary`
4. `content_text`
5. `source_type`
   可选值：`plain_text`、`codex_command`、`compaction`
6. `source_run_id`
7. `is_compacted`
8. `created_at`
9. `updated_at`

说明：

1. `summary` 也是普通消息行，但 `role=summary`。
2. 被压缩进摘要的旧消息不物理删除，只标记 `is_compacted=true`。
3. 上下文组装时，只读取：
   - 最新的一条未压缩 `summary`
   - 所有未压缩的最近原文消息

### 3. `codex_runs`

在现有基础上增加：

1. `conversation_session_id`
2. `resolved_prompt_text`

说明：

1. `prompt_text` 保留“用户原始输入”。
2. `resolved_prompt_text` 记录“真正送给 `codex exec` 的完整 prompt”。
3. 这样后续审计时可以同时看到：
   - 用户原始说了什么
   - 系统实际拼给 Codex 的上下文是什么

## 命令行为

### 普通文本

1. 解析为 `run_codex`
2. 命中或创建 `chat_id` 对应活跃会话
3. 写入一条 `user/plain_text`
4. 触发必要的摘要压缩
5. 组装 `resolved_prompt_text`
6. 创建 `CodexRun`
7. Worker 完成后写回一条 `assistant`

### `/codex ...`

与普通文本一致，只是 `source_type=codex_command`。

### `/new`

新增显式命令，用于手动切会话。

行为：

1. 若当前 `chat_id` 存在活跃会话，则将其关闭并标记为 `reset`
2. 新建一条新的 `active` 会话
3. 返回“会话已重置”结果
4. `/new` 自身不进入会话历史

### 其他工作流命令

保持现状，不写入 `conversation_messages`。

## 空闲超时规则

推荐默认值：

1. `CONVERSATION_IDLE_TIMEOUT_SECONDS=7200`

规则：

1. 收到新的普通文本或 `/codex` 时，查找该 `chat_id` 的 `active` 会话。
2. 若不存在，则创建新会话。
3. 若存在但 `last_message_at` 距今超过超时时间，则关闭旧会话并创建新会话。

## 摘要压缩规则

为了避免引入第二条依赖真实 LLM 的后台链路，第一版摘要压缩采用确定性规则生成：

1. 设定 `CONVERSATION_COMPACT_TRIGGER_COUNT`
2. 设定 `CONVERSATION_KEEP_RECENT_COUNT`
3. 当未压缩原文消息数超过触发阈值时：
   - 保留最近 `KEEP_RECENT_COUNT` 条原文
   - 把更早的未压缩 `user/assistant` 消息压缩进一条 `summary`
   - 原消息打上 `is_compacted=true`

第一版摘要文本采用结构化拼接：

1. 若已有旧 `summary`，先把旧摘要作为前缀
2. 然后追加本轮待压缩消息，按：
   - `user: ...`
   - `assistant: ...`
3. 每条消息做长度裁剪，避免摘要无限膨胀

这不是最终最优摘要质量，但它具备三个优点：

1. 不依赖额外 LLM 调用
2. 行为稳定、易测
3. 结构上已经为以后升级成 LLM compaction 留好接口

## 上下文组装

会话层给 `codex exec` 组装的 `resolved_prompt_text` 采用固定模板：

1. 系统说明：
   说明这是同一飞书 chat 的连续会话，需要结合摘要和最近消息继续回答。
2. 会话摘要：
   如果存在 `summary`，放入摘要块。
3. 最近消息：
   顺序拼接未压缩的 `user/assistant` 原文消息。
4. 当前任务：
   再明确指出最后一条用户输入就是当前需要回答的请求。

这样即使底层仍然是“每次新起一次 `codex exec`”，也能在逻辑上形成正式连续会话。

## 兼容性边界

1. 没有 `chat_id` 的调用维持旧行为，仍按无会话单次执行。
2. 现有 `/create` 工作流完全不受影响。
3. 现有飞书 webhook 和飞书长连接共用同一会话层，不分入口。
4. 当前实现的是“正式会话模型 + 逻辑续接”，不是底层原生 CLI session 复用。

## 后续可扩展点

1. 把确定性摘要升级为 LLM compaction
2. 引入长期记忆层，和短期会话分离
3. 加会话白名单、权限分级、风险命令审计
4. 增加 `/session`、`/history`、`/new` 扩展命令
5. 为同一个 chat 的并发消息增加串行化或乐观锁策略

## 本轮实现边界

本轮只完成：

1. 正式 `Session/Message` 数据模型
2. `run_codex` 共享会话上下文
3. 空闲超时自动切会话
4. `/new` 手动重置
5. 摘要压缩第一版
6. 测试、文档与进度更新

本轮不做：

1. 原生 shell 远程终端
2. 多用户权限系统
3. LLM 生成摘要
4. 会话级并发控制增强
