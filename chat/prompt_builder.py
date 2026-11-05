"""Turn a conversation into the text sent to the model.

The model has no memory: to follow a discussion, the last messages are
written before the new question. Only successful messages are kept.
"""

from chat.schemas import Message, Role

ROLE_LABELS = {Role.USER: "Utilisateur", Role.ASSISTANT: "Assistant"}


def build_prompt(history: list[Message], question: str, max_messages: int) -> str:
    """Return the question alone, or the recent history followed by the question."""
    recent = [m for m in history if not m.failed][-max_messages:] if max_messages > 0 else []
    if not recent:
        return question
    lines = [f"{ROLE_LABELS[m.role]} : {m.content}" for m in recent]
    return "Historique de la conversation :\n" + "\n".join(lines) + f"\n\nNouvelle question : {question}"
