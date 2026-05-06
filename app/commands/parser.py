import shlex

from app.commands.schemas import CommandRequest


COMMAND_MAP = {
    "/create": "create_job",
    "/status": "job_status",
    "/retry": "retry_job",
    "/approve": "approve_job",
    "/cancel": "cancel_job",
    "/assets": "list_assets",
    "/health": "runtime_health",
}


def parse_command_text(text, channel, sender_id, chat_id=None, sender_name=None, request_id=None, trace_id=None):
    tokens = shlex.split(text)
    if not tokens:
        raise ValueError("empty command")
    raw_name = tokens[0]
    command_name = COMMAND_MAP.get(raw_name)
    if command_name is None:
        raise ValueError("unsupported command: " + raw_name)
    arguments = _parse_arguments(command_name, tokens[1:])
    return CommandRequest(
        channel=channel,
        sender_id=sender_id,
        chat_id=chat_id,
        sender_name=sender_name,
        command_name=command_name,
        arguments=arguments,
        raw_text=text,
        request_id=request_id,
        trace_id=trace_id,
    )


def _parse_arguments(command_name, tokens):
    arguments = {}
    for token in tokens:
        if "=" not in token:
            raise ValueError("invalid argument: " + token)
        key, value = token.split("=", 1)
        arguments[key] = value

    if command_name == "create_job":
        return {
            "topic": _require(arguments, "topic"),
            "style_preset": _require(arguments, "style"),
            "target_shot_count": int(_require(arguments, "shots")),
            "image_backend": arguments.get("backend", "comfyui_remote"),
        }
    if command_name in ("job_status", "retry_job", "approve_job", "cancel_job", "list_assets"):
        return {"job_id": int(_require(arguments, "job"))}
    if command_name == "runtime_health":
        return {}
    raise ValueError("unsupported command: " + command_name)


def _require(arguments, key):
    if key not in arguments or arguments[key] == "":
        raise ValueError("missing argument: " + key)
    return arguments[key]
