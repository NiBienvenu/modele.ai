"""In-memory storage of requests (jobs).

Simple and fast for one server. To keep history after a restart or to run
several backend instances, replace this class by a database / Redis version
with the same methods (create, get, update).
"""

import threading
import time
import uuid

from inference.schemas import GenerationResult, Job, JobStatus


class JobStore:
    """Thread-safe dictionary of jobs, with automatic cleanup of old answers."""

    def __init__(self, ttl_seconds: int) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._ttl_seconds = ttl_seconds

    def create(self, prompt: str, metadata: dict | None = None) -> Job:
        """Register a new pending job and return it."""
        job = Job(request_id=uuid.uuid4().hex, prompt=prompt, created_at=time.time(), metadata=metadata or {})
        with self._lock:
            self._remove_expired()
            self._jobs[job.request_id] = job
        return job

    def get(self, request_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(request_id)

    def mark_processing(self, request_id: str) -> None:
        self._update(request_id, status=JobStatus.PROCESSING)

    def mark_completed(self, request_id: str, result: GenerationResult) -> None:
        self._update(request_id, status=JobStatus.COMPLETED, result=result, finished_at=time.time())

    def mark_failed(self, request_id: str, error: str) -> None:
        self._update(request_id, status=JobStatus.FAILED, error=error, finished_at=time.time())

    def _update(self, request_id: str, **changes) -> None:
        with self._lock:
            job = self._jobs.get(request_id)
            if job is None:
                return
            for name, value in changes.items():
                setattr(job, name, value)

    def _remove_expired(self) -> None:
        """Delete finished jobs older than the TTL. Caller must hold the lock."""
        limit = time.time() - self._ttl_seconds
        expired = [rid for rid, job in self._jobs.items() if job.is_finished and job.finished_at < limit]
        for request_id in expired:
            del self._jobs[request_id]
