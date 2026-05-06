import pytest

from app.commands.parser import parse_command_text


def test_parse_create_command_with_quoted_topic():
    command = parse_command_text(
        '/create topic="赛博 武侠" style=cinematic shots=4 backend=third_party',
        channel="feishu",
        sender_id="user-1",
        chat_id="chat-1",
    )

    assert command.command_name == "create_job"
    assert command.arguments["topic"] == "赛博 武侠"
    assert command.arguments["style_preset"] == "cinematic"
    assert command.arguments["target_shot_count"] == 4
    assert command.arguments["image_backend"] == "third_party"


def test_parse_status_command():
    command = parse_command_text(
        "/status job=123",
        channel="feishu",
        sender_id="user-1",
        chat_id="chat-1",
    )

    assert command.command_name == "job_status"
    assert command.arguments["job_id"] == 123


def test_parse_health_command_without_arguments():
    command = parse_command_text(
        "/health",
        channel="feishu",
        sender_id="user-1",
        chat_id="chat-1",
    )

    assert command.command_name == "runtime_health"
    assert command.arguments == {}


def test_parse_command_rejects_unsupported_command():
    with pytest.raises(ValueError):
        parse_command_text(
            "/unknown value=1",
            channel="feishu",
            sender_id="user-1",
            chat_id="chat-1",
        )
