"""Tests of the REST API with a fake engine. Needs fastapi + httpx, no torch.

Run:  python -m unittest discover -s tests/platform -t .
"""

import os
import time
import unittest
from unittest import mock

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover - API deps not installed
    TestClient = None

from config.settings import Settings
from inference.job_store import JobStore
from inference.service import InferenceService
from tests.platform.test_inference_service import PARAMS, FakeEngine


def build_test_client(max_prompt_length: int = 100) -> "TestClient":
    from backend.main import create_app

    with mock.patch.dict(os.environ, {"MAX_PROMPT_LENGTH": str(max_prompt_length)}, clear=True):
        settings = Settings.from_env()
    service = InferenceService(FakeEngine(fail_on="crash"), JobStore(ttl_seconds=60), PARAMS)
    return TestClient(create_app(settings, service))


@unittest.skipIf(TestClient is None, "fastapi is not installed")
class ApiTest(unittest.TestCase):
    def setUp(self):
        self.client = build_test_client()
        self.client.__enter__()  # Runs the lifespan: starts the worker

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def ask(self, prompt: str) -> str:
        reply = self.client.post("/question", json={"prompt": prompt})
        self.assertEqual(reply.status_code, 202, reply.text)
        return reply.json()["request_id"]

    def wait_for(self, request_id: str) -> dict:
        for _ in range(200):
            body = self.client.get(f"/response/{request_id}").json()
            if body["status"] in ("completed", "failed"):
                return body
            time.sleep(0.01)
        self.fail("timeout")

    def test_post_question_returns_request_id(self):
        reply = self.client.post("/question", json={"prompt": "bonjour"})
        self.assertEqual(reply.status_code, 202)
        body = reply.json()
        self.assertEqual(set(body), {"request_id", "status"})

    def test_full_flow_returns_answer_tokens_and_time(self):
        body = self.wait_for(self.ask("bonjour le monde"))
        self.assertEqual(body["status"], "completed")
        self.assertEqual(body["response"], "BONJOUR LE MONDE")
        self.assertEqual(body["tokens"], 3)
        self.assertIsInstance(body["elapsed_time"], float)

    def test_generation_error_is_reported(self):
        body = self.wait_for(self.ask("crash"))
        self.assertEqual(body["status"], "failed")
        self.assertIn("boom", body["error"])

    def test_unknown_request_id_gives_404(self):
        self.assertEqual(self.client.get("/response/nope").status_code, 404)

    def test_empty_prompt_is_rejected(self):
        self.assertEqual(self.client.post("/question", json={"prompt": "   "}).status_code, 422)
        self.assertEqual(self.client.post("/question", json={}).status_code, 422)

    def test_too_long_prompt_is_rejected(self):
        self.assertEqual(self.client.post("/question", json={"prompt": "a" * 101}).status_code, 413)

    def test_cors_allows_frontend(self):
        reply = self.client.get("/response/nope", headers={"Origin": "http://localhost:5173"})
        self.assertEqual(reply.headers.get("access-control-allow-origin"), "http://localhost:5173")


if __name__ == "__main__":
    unittest.main()
