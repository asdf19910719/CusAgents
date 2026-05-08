from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.commands.parser import parse_command_text
from app.commands.router import CommandRouter
from app.db.base import Base
from app.db.models.codex_run import CodexRun
from app.db.models.conversation_message import ConversationMessage
from app.services.codex_run_service import CodexRunService
from app.workers.jobs import execute_codex_run


class FakeDispatcher:
    def enqueue_codex_run(self, run_id):
        return {"dispatch_status": "enqueued", "queue_name": "test-queue"}


def fake_runner(command, cwd, capture_output, text, encoding, errors, check, timeout):
    output_path = Path(command[command.index("-o") + 1])
    output_path.write_text("assistant final answer", encoding="utf-8")

    class Result:
        returncode = 0
        stdout = "assistant final answer"
        stderr = ""

    return Result()


def test_execute_codex_run_writes_assistant_message_back_to_conversation(tmp_path):
    from app.core.config import Settings

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    router = CommandRouter(
        dispatcher=FakeDispatcher(),
        notification_service=None,
        settings=Settings(_env_file=None, LLM_API_KEY="test-key"),
    )
    command = parse_command_text(
        "Continue previous context and answer this question",
        channel="feishu",
        sender_id="ou_test_user",
        chat_id="oc_test_chat",
    )

    with Session(engine) as session:
        result = router.handle(session, command)
        run = session.get(CodexRun, result.run_id)
        conversation_session_id = run.conversation_session_id

    service = CodexRunService(
        command_name="codex",
        runner=fake_runner,
        workdir=".",
        output_dir=str(tmp_path / "codex_runs"),
        generated_images_dir=str(tmp_path / "generated_images"),
    )

    execute_codex_run(
        run_id=result.run_id,
        session_factory=session_factory,
        codex_run_service=service,
        notification_service=None,
    )

    with Session(engine) as session:
        messages = (
            session.query(ConversationMessage)
            .filter_by(session_id=conversation_session_id, is_compacted=False)
            .order_by(ConversationMessage.id.asc())
            .all()
        )

        assert [item.role for item in messages] == ["user", "assistant"]
        assert messages[-1].content_text == "assistant final answer"
