# 飞书 Codex 正式会话实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为飞书普通文本和 `/codex` 建立按 `chat_id` 共享的正式会话层，支持空闲超时、手动重置和摘要压缩。

**Architecture:** 在现有 `CommandRouter -> CodexRun -> Worker -> CodexRunService` 链路之间加入 `ConversationService`。路由层负责命中或创建会话、写入用户消息、生成执行快照 prompt；Worker 负责把 assistant 结果写回会话；摘要压缩由会话服务在写入用户消息时同步完成。

**Tech Stack:** Python 3.11, SQLAlchemy, Alembic, FastAPI, pytest, 现有 Codex CLI 执行链路

---

### Task 1: 补会话命令解析测试

**Files:**
- Modify: `tests/commands/test_command_parser.py`
- Modify: `app/commands/parser.py`

- [ ] **Step 1: 写失败测试，约束 `/new` 命令**

在 `tests/commands/test_command_parser.py` 追加：

```python
def test_parse_new_command():
    command = parse_command_text(
        "/new",
        channel="feishu",
        sender_id="user-1",
        chat_id="chat-1",
    )

    assert command.command_name == "reset_conversation"
    assert command.arguments == {}
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/commands/test_command_parser.py::test_parse_new_command -v`
Expected: FAIL with unsupported command

- [ ] **Step 3: 最小实现 `/new` 解析**

在 `app/commands/parser.py`：

1. 给 `COMMAND_MAP` 增加 `"/new": "reset_conversation"`
2. 在 `_parse_arguments()` 里让 `reset_conversation` 返回空字典

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/commands/test_command_parser.py::test_parse_new_command -v`
Expected: PASS

### Task 2: 补会话模型测试

**Files:**
- Create: `tests/services/test_conversation_service.py`
- Create: `app/db/models/conversation_session.py`
- Create: `app/db/models/conversation_message.py`
- Modify: `app/db/models/__init__.py`
- Modify: `tests/services/test_models.py`

- [ ] **Step 1: 写失败测试，约束会话与消息模型**

创建 `tests/services/test_conversation_service.py`，先写：

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.conversation_session import ConversationSession
from app.db.models.conversation_message import ConversationMessage


def test_conversation_models_can_be_created():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        conversation = ConversationSession(
            chat_id="oc_test_chat",
            status="active",
        )
        session.add(conversation)
        session.flush()

        message = ConversationMessage(
            session_id=conversation.id,
            role="user",
            content_text="hello",
            source_type="plain_text",
            is_compacted=False,
        )
        session.add(message)
        session.commit()

        assert conversation.id is not None
        assert message.id is not None
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/services/test_conversation_service.py::test_conversation_models_can_be_created -v`
Expected: FAIL with import error

- [ ] **Step 3: 最小实现模型**

新增：

1. `app/db/models/conversation_session.py`
2. `app/db/models/conversation_message.py`

并在 `app/db/models/__init__.py` 导出它们。

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/services/test_conversation_service.py::test_conversation_models_can_be_created -v`
Expected: PASS

### Task 3: 补会话服务测试

**Files:**
- Modify: `tests/services/test_conversation_service.py`
- Create: `app/services/conversation_service.py`
- Modify: `app/core/config.py`

- [ ] **Step 1: 写失败测试，约束“同 chat 复用会话”**

在 `tests/services/test_conversation_service.py` 追加：

```python
from app.services.conversation_service import ConversationService


def test_conversation_service_reuses_active_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = ConversationService(
            idle_timeout_seconds=7200,
            compact_trigger_count=20,
            keep_recent_count=12,
        )
        first = service.get_or_create_session(session, chat_id="oc_test_chat")
        second = service.get_or_create_session(session, chat_id="oc_test_chat")

        assert first.id == second.id
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/services/test_conversation_service.py::test_conversation_service_reuses_active_session -v`
Expected: FAIL with missing service

- [ ] **Step 3: 最小实现会话服务和配置项**

新增 `app/services/conversation_service.py`，先实现：

1. `get_or_create_session(session, chat_id)`
2. 构造参数：
   - `idle_timeout_seconds`
   - `compact_trigger_count`
   - `keep_recent_count`

并在 `app/core/config.py` 增加：

1. `CONVERSATION_IDLE_TIMEOUT_SECONDS`
2. `CONVERSATION_COMPACT_TRIGGER_COUNT`
3. `CONVERSATION_KEEP_RECENT_COUNT`

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/services/test_conversation_service.py::test_conversation_service_reuses_active_session -v`
Expected: PASS

### Task 4: 补空闲超时切会话测试

**Files:**
- Modify: `tests/services/test_conversation_service.py`
- Modify: `app/services/conversation_service.py`

- [ ] **Step 1: 写失败测试，约束空闲超时**

在 `tests/services/test_conversation_service.py` 追加：

```python
from datetime import datetime, timedelta


def test_conversation_service_rotates_expired_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = ConversationService(
            idle_timeout_seconds=60,
            compact_trigger_count=20,
            keep_recent_count=12,
        )
        first = service.get_or_create_session(session, chat_id="oc_test_chat", now=datetime(2026, 5, 7, 10, 0, 0))
        second = service.get_or_create_session(session, chat_id="oc_test_chat", now=datetime(2026, 5, 7, 10, 2, 0))

        assert first.id != second.id
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/services/test_conversation_service.py::test_conversation_service_rotates_expired_session -v`
Expected: FAIL because same session reused

- [ ] **Step 3: 实现超时切会话**

在 `ConversationService` 中：

1. `get_or_create_session(..., now=None)` 支持注入时间
2. 若活跃会话超时，则关闭旧会话并创建新会话

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/services/test_conversation_service.py::test_conversation_service_rotates_expired_session -v`
Expected: PASS

### Task 5: 补手动重置测试

**Files:**
- Modify: `tests/services/test_conversation_service.py`
- Modify: `tests/commands/test_command_router.py`
- Modify: `app/services/conversation_service.py`
- Modify: `app/commands/router.py`

- [ ] **Step 1: 写失败测试，约束 `/new` 行为**

在 `tests/commands/test_command_router.py` 追加：

```python
def test_command_router_resets_conversation_for_new_command():
    from app.core.config import Settings

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    router = CommandRouter(
        dispatcher=FakeDispatcher(),
        notification_service=FakeNotificationService(),
        settings=Settings(_env_file=None, LLM_API_KEY="test-key"),
    )
    command = parse_command_text(
        "/new",
        channel="feishu",
        sender_id="ou_test_user",
        chat_id="oc_test_chat",
    )

    with Session(engine) as session:
        result = router.handle(session, command)

        assert result.success is True
        assert result.command_name == "reset_conversation"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/commands/test_command_router.py::test_command_router_resets_conversation_for_new_command -v`
Expected: FAIL with unsupported command

- [ ] **Step 3: 实现路由层 `/new`**

在 `app/commands/router.py`：

1. `_dispatch()` 增加 `reset_conversation`
2. 实现 `_reset_conversation()`
3. 无 `chat_id` 时抛 `ValueError("chat_id required for conversation reset")`

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/commands/test_command_router.py::test_command_router_resets_conversation_for_new_command -v`
Expected: PASS

### Task 6: 补会话上下文组装测试

**Files:**
- Modify: `tests/services/test_conversation_service.py`
- Modify: `app/services/conversation_service.py`

- [ ] **Step 1: 写失败测试，约束上下文组装**

在 `tests/services/test_conversation_service.py` 追加：

```python
def test_conversation_service_builds_resolved_prompt_from_summary_and_recent_messages():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = ConversationService(
            idle_timeout_seconds=7200,
            compact_trigger_count=20,
            keep_recent_count=12,
        )
        conversation = service.get_or_create_session(session, chat_id="oc_test_chat")
        service.append_message(session, conversation, role="summary", content_text="旧摘要", source_type="compaction")
        service.append_message(session, conversation, role="user", content_text="前一条问题", source_type="plain_text")
        service.append_message(session, conversation, role="assistant", content_text="前一条回答", source_type="codex_reply")

        resolved = service.build_resolved_prompt(
            session,
            conversation,
            current_prompt="当前问题",
        )

        assert "旧摘要" in resolved
        assert "前一条问题" in resolved
        assert "前一条回答" in resolved
        assert "当前问题" in resolved
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/services/test_conversation_service.py::test_conversation_service_builds_resolved_prompt_from_summary_and_recent_messages -v`
Expected: FAIL with missing method

- [ ] **Step 3: 实现上下文组装**

在 `ConversationService` 中增加：

1. `append_message(...)`
2. `build_resolved_prompt(...)`
3. 内部按：
   - 摘要
   - 最近消息
   - 当前问题
   组装 prompt

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/services/test_conversation_service.py::test_conversation_service_builds_resolved_prompt_from_summary_and_recent_messages -v`
Expected: PASS

### Task 7: 补摘要压缩测试

**Files:**
- Modify: `tests/services/test_conversation_service.py`
- Modify: `app/services/conversation_service.py`

- [ ] **Step 1: 写失败测试，约束摘要压缩**

在 `tests/services/test_conversation_service.py` 追加：

```python
def test_conversation_service_compacts_old_messages_and_keeps_recent_ones():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = ConversationService(
            idle_timeout_seconds=7200,
            compact_trigger_count=4,
            keep_recent_count=2,
        )
        conversation = service.get_or_create_session(session, chat_id="oc_test_chat")
        service.append_message(session, conversation, role="user", content_text="u1", source_type="plain_text")
        service.append_message(session, conversation, role="assistant", content_text="a1", source_type="codex_reply")
        service.append_message(session, conversation, role="user", content_text="u2", source_type="plain_text")
        service.append_message(session, conversation, role="assistant", content_text="a2", source_type="codex_reply")
        service.append_message(session, conversation, role="user", content_text="u3", source_type="plain_text")

        service.compact_if_needed(session, conversation)

        summary_messages = [item for item in conversation.messages if item.role == "summary" and item.is_compacted is False]
        recent_messages = [item for item in conversation.messages if item.role != "summary" and item.is_compacted is False]

        assert len(summary_messages) == 1
        assert len(recent_messages) == 2
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/services/test_conversation_service.py::test_conversation_service_compacts_old_messages_and_keeps_recent_ones -v`
Expected: FAIL because no compaction exists

- [ ] **Step 3: 实现摘要压缩**

在 `ConversationService` 中增加：

1. `compact_if_needed(...)`
2. `_build_compaction_summary(...)`
3. 只保留一条活动 `summary`

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/services/test_conversation_service.py::test_conversation_service_compacts_old_messages_and_keeps_recent_ones -v`
Expected: PASS

### Task 8: 补 CodexRun 会话绑定测试

**Files:**
- Modify: `tests/commands/test_command_router.py`
- Modify: `app/db/models/codex_run.py`
- Modify: `app/commands/router.py`

- [ ] **Step 1: 写失败测试，约束 run 绑定 session 和 resolved prompt**

在 `tests/commands/test_command_router.py` 现有 `test_command_router_creates_codex_run_and_enqueues_it` 中追加断言：

```python
        assert run.conversation_session_id is not None
        assert run.resolved_prompt_text
        assert "Summarize current blockers" in run.resolved_prompt_text
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/commands/test_command_router.py::test_command_router_creates_codex_run_and_enqueues_it -v`
Expected: FAIL with missing attributes

- [ ] **Step 3: 实现 run 与会话绑定**

1. `CodexRun` 增加：
   - `conversation_session_id`
   - `resolved_prompt_text`
2. `CommandRouter._run_codex()` 中接入 `ConversationService`

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/commands/test_command_router.py::test_command_router_creates_codex_run_and_enqueues_it -v`
Expected: PASS

### Task 9: 补 Worker 写回 assistant 消息测试

**Files:**
- Modify: `tests/services/test_codex_run_service.py`
- Modify: `tests/commands/test_command_router.py`
- Modify: `tests/e2e/test_worker_flow.py`
- Modify: `app/workers/jobs.py`

- [ ] **Step 1: 写失败测试，约束执行完成后写回 assistant**

在 `tests/e2e/test_worker_flow.py` 追加一个最小用例，断言执行后会话里存在 assistant 消息。

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/e2e/test_worker_flow.py -v`
Expected: FAIL because worker does not touch conversation messages

- [ ] **Step 3: 最小实现 Worker 写回**

在 `app/workers/jobs.py` 中：

1. 取 `run.conversation_session_id`
2. 若存在，则调用 `ConversationService.append_message(... role="assistant" ...)`
3. 同步更新会话 `last_message_at`

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/e2e/test_worker_flow.py -v`
Expected: PASS

### Task 10: 补手动重置与无 chat_id 兼容测试

**Files:**
- Modify: `tests/commands/test_command_router.py`
- Modify: `app/commands/router.py`

- [ ] **Step 1: 写失败测试**

追加两个测试：

1. `/new` 在无 `chat_id` 时报错
2. `run_codex` 在无 `chat_id` 时仍可继续旧的无会话行为

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/commands/test_command_router.py -v`
Expected: FAIL on missing compatibility logic

- [ ] **Step 3: 实现兼容边界**

在 `CommandRouter` 中：

1. 无 `chat_id` 时，`run_codex` 不绑定会话
2. `/new` 无 `chat_id` 时抛 `ValueError`

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/commands/test_command_router.py -v`
Expected: PASS

### Task 11: 补迁移和开发态兼容

**Files:**
- Create: `migrations/versions/9f2c6e31b8ab_add_conversation_sessions.py`
- Modify: `app/db/session.py`

- [ ] **Step 1: 写失败测试，约束开发态能创建新表**

在 `tests/services/test_models.py` 或新测试里断言 `Base.metadata.create_all()` 后新表可用。

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/services/test_models.py -v`
Expected: FAIL on missing tables or missing columns

- [ ] **Step 3: 实现迁移与 sqlite 兼容**

1. Alembic 迁移新增两张表
2. 给 `codex_runs` 增加新字段
3. `app/db/session.py` 补 development 兼容建表逻辑

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/services/test_models.py -v`
Expected: PASS

### Task 12: 补飞书入口回归测试

**Files:**
- Modify: `tests/api/test_webhooks_api.py`
- Modify: `tests/channels/test_feishu_long_connection.py`

- [ ] **Step 1: 写失败测试**

补两个回归：

1. 普通文本进入会话
2. `/new` 可通过 webhook 和长连接入口正常触发

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/api/test_webhooks_api.py tests/channels/test_feishu_long_connection.py -v`
Expected: FAIL because new command path not covered

- [ ] **Step 3: 实现必要适配**

如有需要，仅做最小修正，保证两个入口共用同一行为。

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/api/test_webhooks_api.py tests/channels/test_feishu_long_connection.py -v`
Expected: PASS

### Task 13: 更新文档和进度

**Files:**
- Modify: `README.md`
- Modify: `doc/当前系统详细使用说明.md`
- Modify: `doc/协作进度.md`

- [ ] **Step 1: 更新 README**

补充：

1. `chat_id` 共享会话
2. `/new` 命令
3. 会话超时与摘要压缩行为
4. 无 `chat_id` 调用仍为无会话模式

- [ ] **Step 2: 更新使用说明**

同步补：

1. 会话进入规则
2. `/new`
3. 历史压缩边界

- [ ] **Step 3: 更新协作进度**

按项目要求写入：

1. 当前目标
2. 已完成工作
3. 当前状态
4. 下一步
5. 关键文件
6. 阻塞或开放问题

### Task 14: 完整验证

**Files:**
- Test: `tests/commands/test_command_parser.py`
- Test: `tests/commands/test_command_router.py`
- Test: `tests/services/test_conversation_service.py`
- Test: `tests/services/test_models.py`
- Test: `tests/e2e/test_worker_flow.py`
- Test: `tests/api/test_webhooks_api.py`
- Test: `tests/channels/test_feishu_long_connection.py`
- Test: `README.md`

- [ ] **Step 1: 跑针对性测试**

Run:

```bash
pytest tests/commands/test_command_parser.py tests/commands/test_command_router.py tests/services/test_conversation_service.py tests/services/test_models.py tests/e2e/test_worker_flow.py tests/api/test_webhooks_api.py tests/channels/test_feishu_long_connection.py -v
```

Expected: all pass

- [ ] **Step 2: 跑全量回归**

Run:

```bash
pytest -v
```

Expected: all pass

- [ ] **Step 3: 人工复核文档**

检查：

1. `README.md`
2. `doc/当前系统详细使用说明.md`
3. `doc/协作进度.md`

确认命令名、字段名、行为描述与代码一致
