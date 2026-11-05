"""Conversation storage in SQLite (one file in storage/, kept by a Docker volume).

SQLite needs no server and is enough for one backend. To move to
PostgreSQL later, write another class with the same public methods.
Every method opens its own connection, so it is safe to call from the
API threads and from the inference worker thread.
"""

import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from chat.schemas import Conversation, Message, Role

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id          TEXT PRIMARY KEY,
    device_id   TEXT NOT NULL,
    title       TEXT NOT NULL,
    created_at  REAL NOT NULL,
    updated_at  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conversations_device ON conversations (device_id, updated_at);

CREATE TABLE IF NOT EXISTS messages (
    id               TEXT PRIMARY KEY,
    conversation_id  TEXT NOT NULL REFERENCES conversations (id) ON DELETE CASCADE,
    role             TEXT NOT NULL,
    content          TEXT NOT NULL,
    tokens           INTEGER,
    elapsed_time     REAL,
    failed           INTEGER NOT NULL DEFAULT 0,
    created_at       REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages (conversation_id, created_at);
"""


class ConversationRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self._db_path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            yield db
            db.commit()
        finally:
            db.close()

    # ---- Conversations ------------------------------------------------------
    def create_conversation(self, device_id: str, title: str) -> Conversation:
        now = time.time()
        conversation = Conversation(uuid.uuid4().hex, device_id, title, now, now)
        with self._connect() as db:
            db.execute(
                "INSERT INTO conversations VALUES (?, ?, ?, ?, ?)",
                (conversation.conversation_id, device_id, title, now, now),
            )
        return conversation

    def get_conversation(self, conversation_id: str, device_id: str) -> Conversation | None:
        """Conversation with its messages, only if it belongs to this device."""
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM conversations WHERE id = ? AND device_id = ?", (conversation_id, device_id)
            ).fetchone()
            if row is None:
                return None
            rows = db.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at", (conversation_id,)
            ).fetchall()
        return _to_conversation(row, [_to_message(r) for r in rows])

    def list_conversations(self, device_id: str) -> list[Conversation]:
        """Conversations of a device, most recent first (without messages)."""
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM conversations WHERE device_id = ? ORDER BY updated_at DESC", (device_id,)
            ).fetchall()
        return [_to_conversation(row, []) for row in rows]

    def delete_conversation(self, conversation_id: str, device_id: str) -> bool:
        with self._connect() as db:
            cursor = db.execute(
                "DELETE FROM conversations WHERE id = ? AND device_id = ?", (conversation_id, device_id)
            )
        return cursor.rowcount > 0

    # ---- Messages -------------------------------------------------------------
    def add_message(
        self,
        conversation_id: str,
        role: Role,
        content: str,
        tokens: int | None = None,
        elapsed_time: float | None = None,
        failed: bool = False,
    ) -> Message:
        message = Message(uuid.uuid4().hex, conversation_id, role, content, time.time(), tokens, elapsed_time, failed)
        with self._connect() as db:
            db.execute(
                "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    message.message_id,
                    conversation_id,
                    role.value,
                    content,
                    tokens,
                    elapsed_time,
                    int(failed),
                    message.created_at,
                ),
            )
            db.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (message.created_at, conversation_id))
        return message


def _to_conversation(row: sqlite3.Row, messages: list[Message]) -> Conversation:
    return Conversation(row["id"], row["device_id"], row["title"], row["created_at"], row["updated_at"], messages)


def _to_message(row: sqlite3.Row) -> Message:
    return Message(
        message_id=row["id"],
        conversation_id=row["conversation_id"],
        role=Role(row["role"]),
        content=row["content"],
        created_at=row["created_at"],
        tokens=row["tokens"],
        elapsed_time=row["elapsed_time"],
        failed=bool(row["failed"]),
    )
