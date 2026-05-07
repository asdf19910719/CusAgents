import shlex

from app.commands.schemas import CommandRequest


COMMAND_MAP = {
    "/create": "create_job",
    "/codex": "run_codex",
    "/codex_status": "codex_status",
    "/status": "job_status",
    "/retry": "retry_job",
    "/approve": "approve_job",
    "/cancel": "cancel_job",
    "/assets": "list_assets",
    "/health": "runtime_health",
}


def parse_command_text(text, channel, sender_id, chat_id=None, sender_name=None, request_id=None, trace_id=None):
    normalized_text = (text or "").strip()
    tokens = shlex.split(normalized_text)
    if not tokens:
        raise ValueError("empty command")
    raw_name = tokens[0]
    if not raw_name.startswith("/"):
        command_name = "run_codex"
        arguments = {"prompt": normalized_text}
    else:
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
        raw_text=normalized_text,
        request_id=request_id,
        trace_id=trace_id,
    )


def _parse_arguments(command_name, tokens):
    if command_name == "run_codex" and tokens and all("=" not in token for token in tokens):
        return {"prompt": " ".join(tokens).strip()}

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
    if command_name == "run_codex":
        return {"prompt": _require(arguments, "prompt")}
    if command_name == "codex_status":
        return {"run_id": int(_require(arguments, "run"))}
    if command_name in ("job_status", "retry_job", "approve_job", "cancel_job", "list_assets"):
        return {"job_id": int(_require(arguments, "job"))}
    if command_name == "runtime_health":
        return {}
    raise ValueError("unsupported command: " + command_name)


def _require(arguments, key):
    if key not in arguments or arguments[key] == "":
        raise ValueError("missing argument: " + key)
    return arguments[key]
