"""Plain data types shared by the inference layer.

They do not depend on torch, LitGPT or FastAPI, so any layer can use them.
"""

from dataclasses import dataclass, field
from enum import Enum


@dataclass(frozen=True)
class GenerationParams:
    """Sampling options for one generation."""

    max_new_tokens: int
    temperature: float
    top_p: float
    top_k: int | None
    system_prompt: str | None = None


@dataclass(frozen=True)
class GenerationResult:
    """What the engine returns after generating an answer."""

    text: str
    tokens: int  # Number of generated tokens (prompt not included)
    elapsed_time: float  # Seconds spent generating


class JobStatus(str, Enum):
    """Life cycle of a request: pending -> processing -> completed | failed."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    """One question sent by a user and its answer once ready."""

    request_id: str
    prompt: str
    created_at: float
    status: JobStatus = JobStatus.PENDING
    result: GenerationResult | None = None
    error: str | None = None
    finished_at: float | None = field(default=None)

    @property
    def is_finished(self) -> bool:
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED)
