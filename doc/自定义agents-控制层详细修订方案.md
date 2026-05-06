# 自定义 Agents 控制层详细修订方案

## 一、文档目的

这份文档用于补全当前项目中缺失的“控制层”，使系统从“内容生成后端”升级为“可通过飞书/手机远程下发指令并接收结果的可控系统”。

它不是替代现有实施计划，而是对现有 [自定义agents-详细实施计划.md](E:/AIProject/CusAgents/doc/自定义agents-详细实施计划.md) 的增补。

当前项目已经具备的能力是：

1. `Job` 创建与状态查询
2. 故事大纲、分镜、Prompt、出图、审核的生成内核
3. Redis 队列、Worker、成本统计、运行期健康检查
4. `comfyui_remote` 与 `third_party` 两类出图后端

当前项目明显缺失的能力是：

1. 飞书消息入口
2. 手机端控制入口
3. 命令解析层
4. 消息回推与通知
5. 远程访问鉴权

因此，这份修订方案的目标不是“再做一个新系统”，而是：

> 在保留现有生成内核不变的前提下，新增一个位于上层的控制接入层。

---

## 二、重新定义系统分层

### 1. 当前项目实际完成的是生成内核层

当前代码更适合被定义为：

```text
Generation Kernel
  -> jobs api
  -> orchestration
  -> llm/image providers
  -> queue/worker
  -> assets/review/stats
```

它解决的是“任务如何被执行”。

### 2. 原始方案想要的是控制层 + 生成内核层

原始产品意图更接近：

```text
Phone / Feishu
  ->
Control Layer
  ->
Generation Kernel
  ->
Notification / Result Pushback
```

它解决的是：

1. 用户如何下命令
2. 系统如何理解命令
3. 系统如何把命令映射成任务
4. 结果如何返回给用户

### 3. 本次修订后的完整分层

建议把系统正式定义成四层：

```text
Channel Layer
  飞书 Bot / 手机 H5 / Webhook

Command Layer
  指令解析 / 鉴权 / 参数校验 / 命令路由

Execution Layer
  Job API / Orchestration / Worker / Provider

Feedback Layer
  任务通知 / 结果回推 / 审核提醒 / 错误告警
```

---

## 三、修订目标

本次补充应覆盖以下能力：

1. 用户可通过飞书消息创建任务、查询状态、重试任务、审核任务。
2. 用户可通过手机浏览器访问一个轻量控制页，完成同样的基础操作。
3. 控制层不直接耦合具体生成步骤，而是统一转发到现有 `jobs` 与管理接口。
4. 系统能把任务结果、失败信息和审核状态回推到飞书。
5. 外部访问、签名校验和最小权限控制具备明确边界。

---

## 四、明确不在本次修订中完成的内容

为了避免范围失控，以下内容仍不作为本轮必须实现：

1. 不做复杂前端控制台。
2. 不做多租户组织结构。
3. 不做复杂 RBAC 权限系统。
4. 不做完整 IM 会话上下文理解。
5. 不做自然语言自由聊天式 Agent。

本次只做：

1. 命令式控制
2. 基础消息通知
3. 飞书与手机的最小可用入口

---

## 五、推荐的控制层总体架构

```text
飞书消息 / 手机页面 / 外部 webhook
        ->
channel adapters
        ->
command router
        ->
command service
        ->
existing jobs/admin services
        ->
worker / providers
        ->
notification service
        ->
飞书回推 / 手机页面轮询
```

### 1. `Channel Adapters`

职责：

1. 接收不同渠道的输入
2. 转换成统一命令请求对象
3. 不直接执行业务逻辑

建议新增：

1. `FeishuBotAdapter`
2. `MobileWebAdapter`
3. `WebhookAdapter`

### 2. `Command Router`

职责：

1. 按命令类型分发
2. 做参数合法性检查
3. 调用现有生成内核

支持的基础命令建议包括：

1. `create_job`
2. `job_status`
3. `retry_job`
4. `approve_job`
5. `cancel_job`
6. `list_assets`
7. `runtime_health`

### 3. `Notification Service`

职责：

1. 任务创建成功后通知
2. 任务执行失败后通知
3. 任务进入审核后提醒
4. 任务完成后回推结果

---

## 六、飞书控制层设计

### 1. 飞书入口模式

建议同时支持两种模式，但实现顺序有先后：

#### 模式 A：飞书应用机器人

适合：

1. 接收用户消息
2. 解析命令
3. 回推状态

优点：

1. 双向能力完整
2. 更适合“下发命令 + 接收结果”

缺点：

1. 需要事件订阅
2. 需要公网可访问回调地址

#### 模式 B：飞书自定义机器人 Webhook

适合：

1. 只做消息推送
2. 作为通知出口

优点：

1. 实现简单
2. 很适合补通知层

缺点：

1. 不适合作为主要命令入口

### 2. 建议的飞书实现策略

建议采用：

1. 飞书应用机器人作为命令入口
2. 飞书自定义机器人或应用消息接口作为通知出口

也就是说：

> 收命令和发结果可以共用一个飞书应用，但在系统设计上应拆成“输入通道”和“输出通知”两个职责。

### 3. 飞书支持的最小命令格式

建议第一版不要做完全自由自然语言，先做半结构命令：

```text
/create topic=赛博武侠 style=cinematic shots=4 backend=third_party
/status job=123
/retry job=123
/approve job=123
/cancel job=123
/assets job=123
/health
```

后续再逐步支持更自然的写法。

### 4. 飞书消息处理流程

```text
用户发送飞书消息
  ->
Feishu webhook endpoint
  ->
signature verification
  ->
FeishuBotAdapter
  ->
CommandRouter
  ->
Job API / Service
  ->
返回 ack
  ->
异步通知结果
```

### 5. 飞书回推内容建议

任务创建成功：

```text
任务已创建
job_id=123
主题=赛博武侠
镜头数=4
后端=third_party
状态=pending
```

任务完成：

```text
任务已完成
job_id=123
状态=waiting_review / completed
素材数=4
总成本=...
查看地址=...
```

任务失败：

```text
任务失败
job_id=123
失败步骤=image
错误摘要=...
可执行命令=/retry job=123
```

---

## 七、手机控制层设计

### 1. 手机端不建议一开始做 App

优先做：

1. 手机浏览器可访问的 H5 页面
2. 或极简 Web 控制台

因为它只需要做三件事：

1. 提交任务
2. 查看状态
3. 查看结果

### 2. 手机端最小页面结构

建议包含 4 个页面：

1. `Create Job`
2. `Job List`
3. `Job Detail`
4. `Review Action`

### 3. 手机端与后端关系

手机端不应该直连 Worker 或 Provider，只应调用现有 HTTP API。

最小接口复用关系：

1. `POST /jobs`
2. `GET /jobs/{job_id}`
3. `GET /jobs/{job_id}/steps`
4. `GET /jobs/{job_id}/assets`
5. `POST /jobs/{job_id}/retry`
6. `POST /jobs/{job_id}/approve`
7. `POST /jobs/{job_id}/cancel`

### 4. 手机端鉴权建议

建议第一版使用：

1. 单用户访问令牌
2. 短期 session
3. 或飞书登录态映射

不建议第一版就引入复杂账号系统。

---

## 八、命令层设计

### 1. 新增统一命令对象

建议新增 `CommandRequest` 抽象，至少包含：

1. `channel`
2. `sender_id`
3. `sender_name`
4. `command_name`
5. `arguments`
6. `raw_text`
7. `request_id`
8. `trace_id`

### 2. 新增统一命令结果对象

至少包含：

1. `success`
2. `message`
3. `job_id`
4. `status`
5. `payload`
6. `should_notify`

### 3. 命令层与任务层的边界

命令层不直接操作数据库模型，应该调用已有 service 或 API 逻辑。

建议关系如下：

1. `create_job` -> `JobCreationService`
2. `job_status` -> `JobQueryService`
3. `retry_job` -> `RetryService`
4. `approve_job` -> `ReviewService`

若暂时不拆 service，也应至少避免让渠道适配器直接写 ORM。

---

## 九、通知层设计

### 1. 通知类型

至少定义：

1. `job_created`
2. `job_running`
3. `job_waiting_review`
4. `job_completed`
5. `job_failed`
6. `job_cancelled`

### 2. 通知策略

建议第一版做成事件驱动：

1. Job 创建时触发
2. Worker 状态变化时触发
3. 审核状态变化时触发

### 3. 通知目标

建议至少支持：

1. 飞书单聊
2. 飞书群消息
3. 手机页面状态轮询

### 4. 失败通知要求

失败通知必须包含：

1. `job_id`
2. 失败步骤
3. 错误摘要
4. 可重试动作

---

## 十、数据模型补充建议

现有 `Job` 等模型足够支撑生成内核，但不足以支撑控制层。建议新增如下实体。

### 1. `ChannelBinding`

作用：记录用户与渠道标识的映射。

关键字段：

1. `id`
2. `channel_type`
3. `external_user_id`
4. `external_chat_id`
5. `display_name`
6. `is_active`
7. `created_at`

### 2. `CommandLog`

作用：记录每次外部命令输入，便于审计与排错。

关键字段：

1. `id`
2. `request_id`
3. `channel_type`
4. `sender_id`
5. `command_name`
6. `raw_text`
7. `arguments_json`
8. `result_status`
9. `related_job_id`
10. `error_message`
11. `created_at`

### 3. `OutboundNotification`

作用：记录系统向飞书或其他渠道发送的回推消息。

关键字段：

1. `id`
2. `channel_type`
3. `target_id`
4. `event_type`
5. `payload_json`
6. `status`
7. `error_message`
8. `retry_count`
9. `created_at`

### 4. `AccessTokenSession`

如果手机端需要简易登录，可增加：

1. `id`
2. `token`
3. `owner`
4. `expires_at`
5. `is_active`

---

## 十一、API 与模块增补建议

### 1. 新增路由

建议新增：

1. `POST /webhooks/feishu/events`
2. `POST /webhooks/feishu/commands`
3. `GET /mobile/jobs`
4. `GET /mobile/jobs/{job_id}`
5. `POST /mobile/jobs`
6. `POST /mobile/jobs/{job_id}/action`

### 2. 新增目录建议

```text
app/
├─ api/
│  └─ routes/
│     ├─ webhooks.py
│     └─ mobile.py
├─ channels/
│  ├─ feishu/
│  │  ├─ adapter.py
│  │  ├─ verifier.py
│  │  └─ notifier.py
│  └─ mobile/
│     └─ adapter.py
├─ commands/
│  ├─ router.py
│  ├─ parser.py
│  ├─ schemas.py
│  └─ handlers.py
└─ services/
   ├─ notification_service.py
   ├─ command_service.py
   └─ channel_binding_service.py
```

### 3. 现有接口需要补的字段

`GET /jobs/{job_id}` 建议补充：

1. `error_message`
2. `total_cost`
3. `total_input_tokens`
4. `total_output_tokens`
5. `created_at`
6. `updated_at`

否则手机端和飞书端很难直接显示有效摘要。

---

## 十二、安全与公网接入设计

### 1. 飞书入口安全

必须具备：

1. 签名校验
2. 时间戳校验
3. 重放保护

### 2. 手机端安全

必须具备：

1. 基础登录令牌
2. HTTPS
3. 最小权限访问

### 3. 本机服务如何被外部访问

如果你的系统跑在家用电脑或台式机，至少需要一层公网接入方案。建议优先级如下：

1. `Tailscale / ZeroTier`
2. 带鉴权的反向代理
3. 内网穿透

不建议直接裸露本机端口到公网。

### 4. 建议的部署边界

更合理的是：

1. 控制层 webhook 服务可以放在公网可访问环境
2. 生成内核继续跑在本地电脑
3. 二者之间通过受控 API 或隧道通信

这比把整个生成系统裸露出去更安全。

---

## 十三、建议的实施顺序

### Phase 1：先补飞书通知出口

目标：

1. 不接收命令
2. 只在任务创建、失败、完成时推送消息

价值：

1. 最容易落地
2. 可验证通知链路
3. 对现有代码侵入小

### Phase 2：补飞书命令入口

目标：

1. 支持 `/create`、`/status`、`/retry`
2. 验证控制链路

价值：

1. 实现真正远程控制
2. 把飞书从通知工具升级为控制入口

### Phase 3：补手机轻控制页

目标：

1. 手机可发起任务
2. 手机可查状态和看结果

价值：

1. 不依赖飞书时也能操作
2. 为后续管理台打基础

### Phase 4：补命令审计与通知重试

目标：

1. 外部命令可追踪
2. 通知发送失败可重试

价值：

1. 提高稳定性
2. 适合长期使用

---

## 十四、应新增到现有实施计划的任务

建议在原 `Task 16` 之后新增以下任务。

### Task 17：通知层与飞书消息推送

目标：

1. 实现飞书通知发送器
2. 支持任务创建、完成、失败通知
3. 增加通知日志

### Task 18：命令层与统一指令路由

目标：

1. 定义 `CommandRequest`
2. 实现命令解析器
3. 实现 `create/status/retry/approve/cancel/assets/health`

### Task 19：飞书命令入口

目标：

1. 实现飞书 webhook 路由
2. 完成签名校验
3. 完成消息到命令的映射

### Task 20：手机轻控制端

目标：

1. 提供最小 H5 页面或模板页
2. 实现任务提交、列表、详情、审核

### Task 21：安全与公网接入

目标：

1. 增加最小访问控制
2. 明确本机部署与公网入口关系
3. 补充部署说明与风险边界

---

## 十五、修订后的验收标准

补全控制层后，系统的日常可用标准应升级为：

1. 用户可以通过飞书或手机发起任务。
2. 用户可以不登录服务器也能查看任务状态。
3. 系统能在任务完成或失败时主动通知用户。
4. 命令来源、执行结果与通知结果可审计。
5. 控制层故障不会破坏生成内核。

---

## 十六、最终结论

当前项目没有做错，而是只完成了原始产品设想中的“生成内核”。

如果要回到原始 `自定义agents.txt` 更完整的产品目标，必须明确补上：

1. 飞书入口
2. 手机入口
3. 命令层
4. 通知层
5. 外部访问与安全层

这五部分并不是锦上添花，而是决定系统能否真正成为“你可以从手机或飞书控制电脑上 Agents 系统”的关键。

因此，后续迭代应从“继续加生成细节”切换到“补全控制层”。
