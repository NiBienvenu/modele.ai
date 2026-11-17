"""Turn a conversation into the text sent to the model.

The model has no memory: to follow a discussion, the last messages are
written before the new question. Only successful messages are kept.

Two formats (CHAT_PROMPT_FORMAT):
    text   : readable history, for general models
    tokens : the format our own FR-RN model was trained with
             <|user|> Q1 <|assistant|> A1<|endoftext|><|user|> Q2 <|assistant|>
"""

from chat.schemas import Message, Role

ROLE_LABELS = {Role.USER: "Utilisateur", Role.ASSISTANT: "Assistant"}
USER, ASSISTANT, END = "<|user|>", "<|assistant|>", "<|endoftext|>"


def build_prompt(history: list[Message], question: str, max_messages: int, prompt_format: str = "text") -> str:
    """Return the question alone, or the recent history followed by the question."""
    recent = [m for m in history if not m.failed][-max_messages:] if max_messages > 0 else []
    if prompt_format == "tokens":
        return _tokens(recent, question)
    if not recent:
        return question
    lines = [f"{ROLE_LABELS[m.role]} : {m.content}" for m in recent]
    return "Historique de la conversation :\n" + "\n".join(lines) + f"\n\nNouvelle question : {question}"


def _tokens(recent: list[Message], question: str) -> str:
    # The history must start with a user message, like in training
    while recent and recent[0].role != Role.USER:
        recent = recent[1:]
    parts = [
        f"{USER} {m.content} {ASSISTANT}" if m.role == Role.USER else f" {m.content}{END}" for m in recent
    ]
    return "".join(parts) + f"{USER} {question} {ASSISTANT}"
