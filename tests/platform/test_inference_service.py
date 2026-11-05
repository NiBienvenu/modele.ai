"""Tests of the inference service with a fake engine. No torch, no model needed.

Run:  python -m unittest discover -s tests/platform -t .
"""

import time
import unittest

from inference.job_store import JobStore
from inference.schemas import GenerationParams, GenerationResult, JobStatus
from inference.service import InferenceService

PARAMS = GenerationParams(max_new_tokens=10, temperature=0.5, top_p=0.9, top_k=None)


class FakeEngine:
    """Returns the prompt in upper case, or fails if asked to."""

    def __init__(self, fail_on: str | None = None) -> None:
        self.loaded = False
        self.fail_on = fail_on

    def load(self) -> None:
        self.loaded = True

    def generate(self, prompt: str, params: GenerationParams) -> GenerationResult:
        if prompt == self.fail_on:
            raise RuntimeError("boom")
        return GenerationResult(text=prompt.upper(), tokens=len(prompt.split()), elapsed_time=0.01)


def wait_until_finished(service: InferenceService, request_id: str, timeout: float = 2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = service.get_job(request_id)
        if job.is_finished:
            return job
        time.sleep(0.01)
    raise TimeoutError(request_id)


class InferenceServiceTest(unittest.TestCase):
    def setUp(self):
        self.engine = FakeEngine(fail_on="crash")
        self.service = InferenceService(self.engine, JobStore(ttl_seconds=60), PARAMS)
        self.service.start()

    def tearDown(self):
        self.service.stop()

    def test_submit_returns_pending_job_immediately(self):
        job = self.service.submit("hello world")
        self.assertEqual(len(job.request_id), 32)
        self.assertIn(job.status, (JobStatus.PENDING, JobStatus.PROCESSING, JobStatus.COMPLETED))

    def test_job_completes_with_result(self):
        job = wait_until_finished(self.service, self.service.submit("hello world").request_id)
        self.assertTrue(self.engine.loaded)
        self.assertEqual(job.status, JobStatus.COMPLETED)
        self.assertEqual(job.result.text, "HELLO WORLD")
        self.assertEqual(job.result.tokens, 2)

    def test_engine_error_marks_job_failed(self):
        job = wait_until_finished(self.service, self.service.submit("crash").request_id)
        self.assertEqual(job.status, JobStatus.FAILED)
        self.assertIn("boom", job.error)

    def test_unknown_request_returns_none(self):
        self.assertIsNone(self.service.get_job("does-not-exist"))


class JobStoreTest(unittest.TestCase):
    def test_finished_jobs_expire(self):
        store = JobStore(ttl_seconds=0)
        old = store.create("a")
        store.mark_completed(old.request_id, GenerationResult("A", 1, 0.1))
        time.sleep(0.01)
        store.create("b")  # Creating a job triggers the cleanup
        self.assertIsNone(store.get(old.request_id))

    def test_pending_jobs_never_expire(self):
        store = JobStore(ttl_seconds=0)
        pending = store.create("a")
        store.create("b")
        self.assertIsNotNone(store.get(pending.request_id))


if __name__ == "__main__":
    unittest.main()
