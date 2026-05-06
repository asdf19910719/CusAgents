from pydantic import BaseModel, ConfigDict, Field


class CommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: str
    sender_id: str
    chat_id: str | None = None
    sender_name: str | None = None
    command_name: str
    arguments: dict
    raw_text: str
    request_id: str | None = None
    trace_id: str | None = None


class CommandResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    command_name: str
    message: str
    job_id: int | None = None
    status: str | None = None
    payload: dict = Field(default_factory=dict)
