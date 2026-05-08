from datetime import datetime, timedelta

from sqlalchemy import case, func

from app.db.models.codex_run import CodexRun
from app.db.models.conversation_message import ConversationMessage
from app.db.models.conversation_session import ConversationSession


class ConversationService:
    def __init__(self, idle_timeout_seconds, compact_trigger_count, keep_recent_count, retention_seconds=604800, cleanup_batch_size=100):
        self.idle_timeout_seconds = idle_timeout_seconds
        self.compact_trigger_count = compact_trigger_count
        self.keep_recent_count = keep_recent_count
        self.retention_seconds = retention_seconds
        self.cleanup_batch_size = cleanup_batch_size

    def get_or_create_session(self, session, chat_id, now=None, acquire_lock=False):
        current_time = now or datetime.now()
        query = session.query(ConversationSession).filter_by(chat_id=chat_id, status="active").order_by(ConversationSession.id.desc())
        if acquire_lock:
            query = query.with_for_update()
        conversation = query.first()
        if conversation is None:
            conversation = ConversationSession(
                chat_id=chat_id,
                status="active",
                started_at=self._serialize_time(current_time),
                last_message_at=self._serialize_time(current_time),
            )
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            return conversation

        last_message_at = self._deserialize_time(conversation.last_message_at)
        if last_message_at is not None:
            idle_seconds = (current_time - last_message_at).total_seconds()
            if idle_seconds > self.idle_timeout_seconds:
                conversation.status = "expired"
                conversation.closed_at = self._serialize_time(current_time)
                conversation.close_reason = "idle_timeout"
                session.commit()
                replacement = ConversationSession(
                    chat_id=chat_id,
                    status="active",
                    started_at=self._serialize_time(current_time),
                    last_message_at=self._serialize_time(current_time),
                )
                session.add(replacement)
                session.commit()
                session.refresh(replacement)
                return replacement

        return conversation

    def append_message(self, session, conversation, role, content_text, source_type, source_run_id=None):
        message = ConversationMessage(
            session_id=conversation.id,
            role=role,
            content_text=content_text,
            source_type=source_type,
            source_run_id=source_run_id,
            is_compacted=False,
        )
        session.add(message)
        conversation.last_message_at = self._serialize_time(datetime.now())
        session.commit()
        session.refresh(conversation)
        return message

    def build_resolved_prompt(self, session, conversation, current_prompt):
        summary_message = (
            session.query(ConversationMessage)
            .filter_by(session_id=conversation.id, role="summary", is_compacted=False)
            .order_by(ConversationMessage.id.desc())
            .first()
        )
        recent_messages = (
            session.query(ConversationMessage)
            .filter_by(session_id=conversation.id, is_compacted=False)
            .filter(ConversationMessage.role != "summary")
            .order_by(ConversationMessage.id.asc())
            .all()
        )

        lines = [
            "你正在处理同一个飞书 chat 的连续会话。",
            "请结合已有摘要和最近消息继续回答，不要忽略之前已经确认的上下文。",
        ]
        if summary_message is not None:
            lines.extend(
                [
                    "",
                    "[会话摘要]",
                    summary_message.content_text,
                ]
            )
        if recent_messages:
            lines.append("")
            lines.append("[最近消息]")
            for item in recent_messages:
                lines.append("{0}: {1}".format(item.role, item.content_text))
        lines.extend(
            [
                "",
                "[当前任务]",
                current_prompt,
            ]
        )
        return "\n".join(lines)

    def compact_if_needed(self, session, conversation):
        active_messages = (
            session.query(ConversationMessage)
            .filter_by(session_id=conversation.id, is_compacted=False)
            .filter(ConversationMessage.role != "summary")
            .order_by(ConversationMessage.id.asc())
            .all()
        )
        if len(active_messages) <= self.compact_trigger_count:
            return None

        messages_to_keep = active_messages[-self.keep_recent_count :]
        keep_ids = {item.id for item in messages_to_keep}
        messages_to_compact = [item for item in active_messages if item.id not in keep_ids]
        if not messages_to_compact:
            return None

        existing_summary = (
            session.query(ConversationMessage)
            .filter_by(session_id=conversation.id, role="summary", is_compacted=False)
            .order_by(ConversationMessage.id.desc())
            .first()
        )
        summary_text = self._build_compaction_summary(existing_summary, messages_to_compact)
        if existing_summary is not None:
            existing_summary.is_compacted = True

        summary_message = ConversationMessage(
            session_id=conversation.id,
            role="summary",
            content_text=summary_text,
            source_type="compaction",
            source_run_id=None,
            is_compacted=False,
        )
        session.add(summary_message)
        for item in messages_to_compact:
            item.is_compacted = True
        session.commit()
        session.refresh(conversation)
        return summary_message

    def reset_session(self, session, chat_id, now=None, acquire_lock=False):
        current_time = now or datetime.now()
        query = session.query(ConversationSession).filter_by(chat_id=chat_id, status="active").order_by(ConversationSession.id.desc())
        if acquire_lock:
            query = query.with_for_update()
        conversation = query.first()
        if conversation is not None:
            conversation.status = "reset"
            conversation.closed_at = self._serialize_time(current_time)
            conversation.close_reason = "manual_reset"
            session.commit()

        replacement = ConversationSession(
            chat_id=chat_id,
            status="active",
            started_at=self._serialize_time(current_time),
            last_message_at=self._serialize_time(current_time),
        )
        session.add(replacement)
        session.commit()
        session.refresh(replacement)
        return replacement

    def build_session_overview(self, session, conversation_id):
        conversation = session.get(ConversationSession, conversation_id)
        if conversation is None:
            raise ValueError("conversation session not found")

        counts = (
            session.query(
                func.sum(case((ConversationMessage.is_compacted.is_(False), 1), else_=0)),
                func.sum(case((ConversationMessage.is_compacted.is_(True), 1), else_=0)),
            )
            .filter(ConversationMessage.session_id == conversation.id, ConversationMessage.role != "summary")
            .one()
        )
        latest_summary = (
            session.query(ConversationMessage)
            .filter_by(session_id=conversation.id, role="summary", is_compacted=False)
            .order_by(ConversationMessage.id.desc())
            .first()
        )
        source_run_ids = [
            item[0]
            for item in session.query(ConversationMessage.source_run_id)
            .filter(
                ConversationMessage.session_id == conversation.id,
                ConversationMessage.source_run_id.is_not(None),
            )
            .distinct()
            .order_by(ConversationMessage.source_run_id.asc())
            .all()
        ]
        return {
            "session_id": conversation.id,
            "chat_id": conversation.chat_id,
            "status": conversation.status,
            "started_at": conversation.started_at,
            "last_message_at": conversation.last_message_at,
            "closed_at": conversation.closed_at,
            "close_reason": conversation.close_reason,
            "active_message_count": int(counts[0] or 0),
            "compacted_message_count": int(counts[1] or 0),
            "has_summary": latest_summary is not None,
            "latest_summary_text": latest_summary.content_text if latest_summary is not None else None,
            "source_run_ids": source_run_ids,
        }

    def list_session_overviews(self, session, limit=20):
        conversations = session.query(ConversationSession).order_by(ConversationSession.id.desc()).limit(limit).all()
        return [self.build_session_overview(session, item.id) for item in conversations]

    def cleanup_sessions(self, session, now=None, retention_seconds=None, batch_size=None):
        current_time = now or datetime.now()
        retention_seconds = retention_seconds if retention_seconds is not None else self.retention_seconds
        batch_size = batch_size if batch_size is not None else self.cleanup_batch_size
        cutoff = current_time - timedelta(seconds=retention_seconds)

        expired_session_count = 0
        closed_sessions = (
            session.query(ConversationSession)
            .filter(ConversationSession.status == "active")
            .filter(ConversationSession.last_message_at.is_not(None))
            .limit(batch_size)
            .all()
        )
        for conversation in closed_sessions:
            last_message_at = self._deserialize_time(conversation.last_message_at)
            if last_message_at is None:
                continue
            if (current_time - last_message_at).total_seconds() > self.idle_timeout_seconds:
                conversation.status = "expired"
                conversation.closed_at = self._serialize_time(current_time)
                conversation.close_reason = "idle_timeout_cleanup"
                expired_session_count += 1

        old_sessions = (
            session.query(ConversationSession)
            .filter(ConversationSession.status != "active")
            .filter(ConversationSession.closed_at.is_not(None))
            .limit(batch_size)
            .all()
        )
        deleted_session_count = 0
        deleted_message_count = 0
        detached_run_count = 0
        for conversation in old_sessions:
            closed_at = self._deserialize_time(conversation.closed_at)
            if closed_at is None or closed_at > cutoff:
                continue
            detached_run_count += session.query(CodexRun).filter_by(conversation_session_id=conversation.id).update(
                {CodexRun.conversation_session_id: None}, synchronize_session=False
            )
            deleted_message_count += session.query(ConversationMessage).filter_by(session_id=conversation.id).delete(
                synchronize_session=False
            )
            session.delete(conversation)
            deleted_session_count += 1

        session.commit()
        return {
            "expired_session_count": expired_session_count,
            "deleted_session_count": deleted_session_count,
            "deleted_message_count": deleted_message_count,
            "detached_run_count": detached_run_count,
            "retention_seconds": retention_seconds,
            "batch_size": batch_size,
        }

    def _build_compaction_summary(self, existing_summary, messages_to_compact):
        lines = []
        if existing_summary is not None and existing_summary.content_text:
            lines.append("已有摘要:")
            lines.append(existing_summary.content_text[:4000])
        lines.append("新增摘要:")
        for item in messages_to_compact:
            lines.append("{0}: {1}".format(item.role, item.content_text[:500]))
        return "\n".join(lines)

    @staticmethod
    def _serialize_time(value):
        if value is None:
            return None
        return value.isoformat(timespec="seconds")

    @staticmethod
    def _deserialize_time(value):
        if not value:
            return None
        return datetime.fromisoformat(value)
