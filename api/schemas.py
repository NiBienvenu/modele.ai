"""JSON shapes of the REST API (request and response bodies).

These are the public contract with the frontend and external clients.
Change them carefully: the web interface depends on these field names
(see frontend/src/api/types.ts).
"""

from pydantic import BaseModel, Field

from chat.schemas import Conversation, Message, Role
from inference.schemas import Job, JobStatus


# ---- Questions / answers --------------------------------------------------------
class QuestionRequest(BaseModel):
    """Body of POST /question."""

    prompt: str = Field(..., min_length=1, description="The question or instruction sent to the model")
    conversation_id: str | None = Field(None, description="Continue this conversation (empty = new one)")


class QuestionAccepted(BaseModel):
    """Answer of POST /question: the request is queued."""

    request_id: str
    status: JobStatus
    conversation_id: str


class ResponseOut(BaseModel):
    """Answer of GET /response/{request_id}.

    `response`, `tokens` and `elapsed_time` are filled once `status` is "completed".
    While the model is working they are null, so the client polls again.
    """

    request_id: str
    status: JobStatus
    conversation_id: str | None = None
    response: str | None = None
    tokens: int | None = None
    elapsed_time: float | None = Field(None, description="Generation time in seconds")
    error: str | None = None

    @classmethod
    def from_job(cls, job: Job) -> "ResponseOut":
        result = job.result
        return cls(
            request_id=job.request_id,
            status=job.status,
            conversation_id=job.metadata.get("conversation_id"),
            response=result.text if result else None,
            tokens=result.tokens if result else None,
            elapsed_time=result.elapsed_time if result else None,
            error=job.error,
        )


# ---- Conversations ------------------------------------------------------------------
class MessageOut(BaseModel):
    id: str
    role: Role
    content: str
    created_at: float
    tokens: int | None = None
    elapsed_time: float | None = None
    failed: bool = False

    @classmethod
    def from_message(cls, message: Message) -> "MessageOut":
        return cls(
            id=message.message_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
            tokens=message.tokens,
            elapsed_time=message.elapsed_time,
            failed=message.failed,
        )


class ConversationSummary(BaseModel):
    """One line of the conversation list (sidebar)."""

    id: str
    title: str
    updated_at: float

    @classmethod
    def from_conversation(cls, conversation: Conversation) -> "ConversationSummary":
        return cls(id=conversation.conversation_id, title=conversation.title, updated_at=conversation.updated_at)


class ConversationOut(ConversationSummary):
    """A full conversation with its messages."""

    messages: list[MessageOut]

    @classmethod
    def from_conversation(cls, conversation: Conversation) -> "ConversationOut":
        return cls(
            id=conversation.conversation_id,
            title=conversation.title,
            updated_at=conversation.updated_at,
            messages=[MessageOut.from_message(m) for m in conversation.messages],
        )
