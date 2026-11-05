"""JSON shapes of the REST API (request and response bodies).

These are the public contract with the frontend and external clients.
Change them carefully: the web interface depends on these field names.
"""

from pydantic import BaseModel, Field

from inference.schemas import Job, JobStatus


class QuestionRequest(BaseModel):
    """Body of POST /question."""

    prompt: str = Field(..., min_length=1, description="The question or instruction sent to the model")


class QuestionAccepted(BaseModel):
    """Answer of POST /question: the request is queued."""

    request_id: str
    status: JobStatus


class ResponseOut(BaseModel):
    """Answer of GET /response/{request_id}.

    `response`, `tokens` and `elapsed_time` are filled once `status` is "completed".
    While the model is working they are null, so the client polls again.
    """

    request_id: str
    status: JobStatus
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
            response=result.text if result else None,
            tokens=result.tokens if result else None,
            elapsed_time=result.elapsed_time if result else None,
            error=job.error,
        )
