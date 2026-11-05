"""Plain data types of conversations. No framework dependency."""

from dataclasses import dataclass, field
from enum import Enum


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class Message:
    message_id: str
    conversation_id: str
    role: Role
    content: str
    created_at: float
    tokens: int | None = None
    elapsed_time: float | None = None
    failed: bool = False


@dataclass(frozen=True)
class Conversation:
    conversation_id: str
    device_id: str
    title: str
    created_at: float
    updated_at: float
    messages: list[Message] = field(default_factory=list)
