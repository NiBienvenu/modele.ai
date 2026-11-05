"""Chat service: the conversation logic used by the API.

    ask(device, question, conversation?)
        1. finds or creates the conversation (title = start of the question)
        2. saves the user message
        3. builds the prompt with the recent history
        4. queues it in the InferenceService
    when the job ends, the answer (or error) is saved in the conversation.

No login: a conversation belongs to the device_id sent by the browser.
"""

import logging
from dataclasses import dataclass

from chat.prompt_builder import build_prompt
from chat.repository import ConversationRepository
from chat.schemas import Conversation, Role
from config.settings import ChatSettings
from inference.schemas import Job, JobStatus
from inference.service import InferenceService

logger = logging.getLogger(__name__)


class ConversationNotFound(Exception):
    """Unknown conversation, or it belongs to another device."""


@dataclass(frozen=True)
class AskResult:
    job: Job
    conversation_id: str


class ChatService:
    def __init__(self, repository: ConversationRepository, inference: InferenceService, settings: ChatSettings):
        self._repository = repository
        self._inference = inference
        self._settings = settings
        inference.add_listener(self._save_answer)

    # ---- Questions -------------------------------------------------------------
    def ask(self, device_id: str, question: str, conversation_id: str | None = None) -> AskResult:
        conversation = self._get_or_create(device_id, question, conversation_id)
        prompt = build_prompt(conversation.messages, question, self._settings.history_messages)
        self._repository.add_message(conversation.conversation_id, Role.USER, question)
        job = self._inference.submit(prompt, metadata={"conversation_id": conversation.conversation_id})
        return AskResult(job=job, conversation_id=conversation.conversation_id)

    def _get_or_create(self, device_id: str, question: str, conversation_id: str | None) -> Conversation:
        if conversation_id is None:
            return self._repository.create_conversation(device_id, self._make_title(question))
        conversation = self._repository.get_conversation(conversation_id, device_id)
        if conversation is None:
            raise ConversationNotFound(conversation_id)
        return conversation

    def _make_title(self, question: str) -> str:
        title = " ".join(question.split())
        limit = self._settings.title_length
        return title if len(title) <= limit else title[: limit - 1].rstrip() + "…"

    # ---- Answers (called by the inference worker) -----------------------------
    def _save_answer(self, job: Job) -> None:
        conversation_id = job.metadata.get("conversation_id")
        if conversation_id is None:
            return
        if job.status == JobStatus.COMPLETED:
            result = job.result
            self._repository.add_message(
                conversation_id, Role.ASSISTANT, result.text, result.tokens, result.elapsed_time
            )
        else:
            self._repository.add_message(conversation_id, Role.ASSISTANT, job.error or "Erreur", failed=True)

    # ---- Conversations -----------------------------------------------------------
    def list_conversations(self, device_id: str) -> list[Conversation]:
        return self._repository.list_conversations(device_id)

    def get_conversation(self, device_id: str, conversation_id: str) -> Conversation:
        conversation = self._repository.get_conversation(conversation_id, device_id)
        if conversation is None:
            raise ConversationNotFound(conversation_id)
        return conversation

    def delete_conversation(self, device_id: str, conversation_id: str) -> None:
        if not self._repository.delete_conversation(conversation_id, device_id):
            raise ConversationNotFound(conversation_id)
