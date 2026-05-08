from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.codex_run import CodexRun
from app.db.models.conversation_message import ConversationMessage
from app.db.models.conversation_session import ConversationSession
from app.services.conversation_service import ConversationService


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


def test_conversation_service_gets_or_creates_session_with_lock():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = ConversationService(
            idle_timeout_seconds=7200,
            compact_trigger_count=20,
            keep_recent_count=12,
        )
        conversation = service.get_or_create_session(session, chat_id="oc_test_chat", acquire_lock=True)

        assert conversation.id is not None


def test_conversation_service_collects_conversation_overview():
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
        service.append_message(session, conversation, role="assistant", content_text="a1", source_type="codex_reply", source_run_id=11)
        service.append_message(session, conversation, role="user", content_text="u2", source_type="plain_text")
        service.append_message(session, conversation, role="assistant", content_text="a2", source_type="codex_reply", source_run_id=12)
        service.append_message(session, conversation, role="user", content_text="u3", source_type="plain_text")
        service.compact_if_needed(session, conversation)

        overview = service.build_session_overview(session, conversation.id)

        assert overview["session_id"] == conversation.id
        assert overview["chat_id"] == "oc_test_chat"
        assert overview["status"] == "active"
        assert overview["active_message_count"] == 2
        assert overview["compacted_message_count"] == 3
        assert overview["has_summary"] is True
        assert overview["latest_summary_text"]
        assert overview["source_run_ids"] == [11, 12]


def test_conversation_service_cleanup_expires_idle_sessions_and_deletes_old_closed_ones():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = ConversationService(
            idle_timeout_seconds=60,
            compact_trigger_count=20,
            keep_recent_count=12,
            retention_seconds=3600,
            cleanup_batch_size=50,
        )
        active = service.get_or_create_session(session, chat_id="oc_active", now=datetime(2026, 5, 7, 10, 0, 0))
        active.last_message_at = "2026-05-07T10:00:00"

        old_closed = ConversationSession(
            chat_id="oc_old_closed",
            status="expired",
            started_at="2026-05-06T08:00:00",
            last_message_at="2026-05-06T08:10:00",
            closed_at="2026-05-06T08:30:00",
            close_reason="idle_timeout",
        )
        session.add(old_closed)
        session.commit()
        session.refresh(old_closed)

        session.add(
            ConversationMessage(
                session_id=old_closed.id,
                role="user",
                content_text="old message",
                source_type="plain_text",
                is_compacted=False,
            )
        )
        session.add(
            CodexRun(
                request_id="cleanup-run-1",
                channel_type="feishu",
                sender_id="ou_test_user",
                notification_target_id="oc_old_closed",
                conversation_session_id=old_closed.id,
                prompt_text="old prompt",
                status="completed",
            )
        )
        session.commit()

        result = service.cleanup_sessions(session, now=datetime(2026, 5, 7, 12, 0, 0))
        refreshed_active = session.get(ConversationSession, active.id)
        detached_run = session.query(CodexRun).filter_by(request_id="cleanup-run-1").one()

        assert result["expired_session_count"] == 1
        assert result["deleted_session_count"] == 1
        assert result["deleted_message_count"] == 1
        assert result["detached_run_count"] == 1
        assert refreshed_active.status == "expired"
        assert refreshed_active.close_reason == "idle_timeout_cleanup"
        assert session.get(ConversationSession, old_closed.id) is None
        assert detached_run.conversation_session_id is None
