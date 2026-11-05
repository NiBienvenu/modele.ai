"""Tests of the conversation logic (prompt building, title, storage). No torch.

Run:  python -m unittest discover -s tests/platform -t .
"""

import tempfile
import unittest
from pathlib import Path

from chat.prompt_builder import build_prompt
from chat.repository import ConversationRepository
from chat.schemas import Message, Role


def message(role: Role, content: str, failed: bool = False) -> Message:
    return Message("id", "conv", role, content, 0.0, failed=failed)


class PromptBuilderTest(unittest.TestCase):
    def test_first_question_is_sent_alone(self):
        self.assertEqual(build_prompt([], "Bonjour", 6), "Bonjour")

    def test_history_comes_before_the_question(self):
        history = [message(Role.USER, "Q1"), message(Role.ASSISTANT, "R1")]
        prompt = build_prompt(history, "Q2", 6)
        self.assertIn("Utilisateur : Q1\nAssistant : R1", prompt)
        self.assertTrue(prompt.endswith("Nouvelle question : Q2"))

    def test_only_recent_and_successful_messages_are_kept(self):
        history = [message(Role.USER, "old"), message(Role.ASSISTANT, "error", failed=True), message(Role.USER, "new")]
        prompt = build_prompt(history, "Q", 1)
        self.assertIn("new", prompt)
        self.assertNotIn("old", prompt)
        self.assertNotIn("error", prompt)


class RepositoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = ConversationRepository(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.tmp.cleanup()

    def test_messages_are_saved_in_order(self):
        conv = self.repo.create_conversation("device-1", "Titre")
        self.repo.add_message(conv.conversation_id, Role.USER, "Q")
        self.repo.add_message(conv.conversation_id, Role.ASSISTANT, "R", tokens=3, elapsed_time=0.5)
        saved = self.repo.get_conversation(conv.conversation_id, "device-1")
        self.assertEqual([m.content for m in saved.messages], ["Q", "R"])
        self.assertEqual(saved.messages[1].tokens, 3)

    def test_data_survives_a_new_repository(self):
        conv = self.repo.create_conversation("device-1", "Titre")
        reopened = ConversationRepository(Path(self.tmp.name) / "test.db")
        self.assertIsNotNone(reopened.get_conversation(conv.conversation_id, "device-1"))

    def test_deleting_a_conversation_deletes_its_messages(self):
        conv = self.repo.create_conversation("device-1", "Titre")
        self.repo.add_message(conv.conversation_id, Role.USER, "Q")
        self.assertTrue(self.repo.delete_conversation(conv.conversation_id, "device-1"))
        self.assertIsNone(self.repo.get_conversation(conv.conversation_id, "device-1"))


if __name__ == "__main__":
    unittest.main()
