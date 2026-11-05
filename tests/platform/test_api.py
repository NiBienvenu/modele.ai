"""Tests of the REST API with a fake engine. Needs fastapi + httpx, no torch.

Run:  python -m unittest discover -s tests/platform -t .
"""

import os
import tempfile
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

DEVICE = {"X-Device-Id": "device-aaaa-1111"}
OTHER_DEVICE = {"X-Device-Id": "device-bbbb-2222"}


@unittest.skipIf(TestClient is None, "fastapi is not installed")
class ApiTest(unittest.TestCase):
    def setUp(self):
        from backend.main import create_app

        self.tmp = tempfile.TemporaryDirectory()
        env = {"MAX_PROMPT_LENGTH": "100", "STORAGE_DIR": self.tmp.name, "FRONTEND_DIR": self.tmp.name}
        with mock.patch.dict(os.environ, env, clear=True):
            settings = Settings.from_env()
        service = InferenceService(FakeEngine(fail_on="crash"), JobStore(ttl_seconds=60), PARAMS)
        self.client = TestClient(create_app(settings, service))
        self.client.__enter__()  # Runs the lifespan: starts the worker

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.tmp.cleanup()

    # ---- helpers ----
    def ask(self, prompt: str, conversation_id: str | None = None, headers=DEVICE) -> dict:
        reply = self.client.post("/question", json={"prompt": prompt, "conversation_id": conversation_id}, headers=headers)
        self.assertEqual(reply.status_code, 202, reply.text)
        return reply.json()

    def wait_for(self, request_id: str) -> dict:
        for _ in range(200):
            body = self.client.get(f"/response/{request_id}").json()
            if body["status"] in ("completed", "failed"):
                time.sleep(0.02)  # Let the listener save the answer
                return body
            time.sleep(0.01)
        self.fail("timeout")

    # ---- questions / answers ----
    def test_post_question_returns_request_and_conversation_ids(self):
        body = self.ask("bonjour")
        self.assertEqual(set(body), {"request_id", "status", "conversation_id"})

    def test_full_flow_returns_answer_tokens_and_time(self):
        body = self.wait_for(self.ask("bonjour le monde")["request_id"])
        self.assertEqual(body["status"], "completed")
        self.assertEqual(body["response"], "BONJOUR LE MONDE")
        self.assertEqual(body["tokens"], 3)
        self.assertIsInstance(body["elapsed_time"], float)

    def test_generation_error_is_reported(self):
        body = self.wait_for(self.ask("crash")["request_id"])
        self.assertEqual(body["status"], "failed")
        self.assertIn("boom", body["error"])

    def test_unknown_request_id_gives_404(self):
        self.assertEqual(self.client.get("/response/nope").status_code, 404)

    def test_device_id_is_required_and_validated(self):
        self.assertEqual(self.client.post("/question", json={"prompt": "a"}).status_code, 422)
        bad = {"X-Device-Id": "bad id!"}
        self.assertEqual(self.client.post("/question", json={"prompt": "a"}, headers=bad).status_code, 400)

    def test_invalid_prompts_are_rejected(self):
        self.assertEqual(self.client.post("/question", json={"prompt": "   "}, headers=DEVICE).status_code, 422)
        self.assertEqual(self.client.post("/question", json={"prompt": "a" * 101}, headers=DEVICE).status_code, 413)

    # ---- conversations ----
    def test_conversation_keeps_questions_and_answers(self):
        first = self.ask("première question")
        self.wait_for(first["request_id"])
        second = self.ask("deuxième", conversation_id=first["conversation_id"])
        self.assertEqual(second["conversation_id"], first["conversation_id"])
        self.wait_for(second["request_id"])

        conversation = self.client.get(f"/conversations/{first['conversation_id']}", headers=DEVICE).json()
        self.assertEqual(conversation["title"], "première question")
        roles = [m["role"] for m in conversation["messages"]]
        self.assertEqual(roles, ["user", "assistant", "user", "assistant"])
        self.assertEqual(conversation["messages"][1]["content"], "PREMIÈRE QUESTION")

    def test_history_is_sent_to_the_model(self):
        first = self.ask("alpha")
        self.wait_for(first["request_id"])
        second = self.wait_for(self.ask("beta", conversation_id=first["conversation_id"])["request_id"])
        self.assertIn("ALPHA", second["response"])  # The fake engine echoes the full prompt

    def test_failed_answer_is_saved_as_failed_message(self):
        first = self.ask("crash")
        self.wait_for(first["request_id"])
        messages = self.client.get(f"/conversations/{first['conversation_id']}", headers=DEVICE).json()["messages"]
        self.assertTrue(messages[1]["failed"])

    def test_conversations_are_listed_per_device(self):
        self.ask("chez moi")
        self.ask("ailleurs", headers=OTHER_DEVICE)
        mine = self.client.get("/conversations", headers=DEVICE).json()
        self.assertEqual([c["title"] for c in mine], ["chez moi"])

    def test_other_device_cannot_read_or_continue_a_conversation(self):
        conversation_id = self.ask("secret")["conversation_id"]
        self.assertEqual(self.client.get(f"/conversations/{conversation_id}", headers=OTHER_DEVICE).status_code, 404)
        reply = self.client.post(
            "/question", json={"prompt": "x", "conversation_id": conversation_id}, headers=OTHER_DEVICE
        )
        self.assertEqual(reply.status_code, 404)

    def test_delete_conversation(self):
        conversation_id = self.ask("à supprimer")["conversation_id"]
        self.assertEqual(self.client.delete(f"/conversations/{conversation_id}", headers=DEVICE).status_code, 204)
        self.assertEqual(self.client.get(f"/conversations/{conversation_id}", headers=DEVICE).status_code, 404)
        self.assertEqual(self.client.delete(f"/conversations/{conversation_id}", headers=DEVICE).status_code, 404)

    def test_cors_allows_frontend(self):
        reply = self.client.get("/response/nope", headers={"Origin": "http://localhost:5555"})
        self.assertEqual(reply.headers.get("access-control-allow-origin"), "http://localhost:5555")


if __name__ == "__main__":
    unittest.main()
