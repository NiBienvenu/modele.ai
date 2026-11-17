"""Conversation storage in SQLite: one database file per device.

    backend/conversations/<device_id>.db   (kept by a Docker volume)

SQLite needs no server and is enough for one backend. To move to
PostgreSQL later, write another class with the same public methods.
Every method opens its own connection, so it is safe to call from the
API threads and from the inference worker thread.
"""

import re
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


# Same rule as the X-Device-Id header: the id is safe to use as a file name.
SAFE_DEVICE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class ConversationRepository:
    def __init__(self, folder: Path) -> None:
        self._folder = folder
        folder.mkdir(parents=True, exist_ok=True)

    def db_path(self, device_id: str) -> Path:
        if not SAFE_DEVICE_ID.match(device_id):
            raise ValueError(f"Invalid device id: {device_id!r}")
        return self._folder / f"{device_id}.db"

    @contextmanager
    def _connect(self, device_id: str):
        path = self.db_path(device_id)
        db = sqlite3.connect(path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        # Every time (cheap): the file may have been deleted or emptied meanwhile
        db.executescript(SCHEMA)
        try:
            yield db
            db.commit()
        finally:
            db.close()

    def import_old_database(self, old_path: Path) -> int:
        """Split the old shared conversations.db into one file per device (run once)."""
        old = sqlite3.connect(old_path)
        old.row_factory = sqlite3.Row
        try:
            devices = [r[0] for r in old.execute("SELECT DISTINCT device_id FROM conversations")]
            for device_id in devices:
                if not SAFE_DEVICE_ID.match(device_id):
                    continue
                conversations = old.execute("SELECT * FROM conversations WHERE device_id = ?", (device_id,)).fetchall()
                messages = old.execute(
                    "SELECT m.* FROM messages m JOIN conversations c ON c.id = m.conversation_id WHERE c.device_id = ?",
                    (device_id,),
                ).fetchall()
                with self._connect(device_id) as db:
                    db.executemany("INSERT OR IGNORE INTO conversations VALUES (?, ?, ?, ?, ?)", [tuple(r) for r in conversations])
                    db.executemany("INSERT OR IGNORE INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [tuple(r) for r in messages])
        finally:
            old.close()
        old_path.rename(old_path.with_suffix(".db.migrated"))
        return len(devices)

    # ---- Conversations ------------------------------------------------------
    def create_conversation(self, device_id: str, title: str) -> Conversation:
        now = time.time()
        conversation = Conversation(uuid.uuid4().hex, device_id, title, now, now)
        with self._connect(device_id) as db:
            db.execute(
                "INSERT INTO conversations VALUES (?, ?, ?, ?, ?)",
                (conversation.conversation_id, device_id, title, now, now),
            )
        return conversation

    def get_conversation(self, conversation_id: str, device_id: str) -> Conversation | None:
        """Conversation with its messages, only if it belongs to this device."""
        with self._connect(device_id) as db:
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
        with self._connect(device_id) as db:
            rows = db.execute(
                "SELECT * FROM conversations WHERE device_id = ? ORDER BY updated_at DESC", (device_id,)
            ).fetchall()
        return [_to_conversation(row, []) for row in rows]

    def delete_conversation(self, conversation_id: str, device_id: str) -> bool:
        with self._connect(device_id) as db:
            cursor = db.execute(
                "DELETE FROM conversations WHERE id = ? AND device_id = ?", (conversation_id, device_id)
            )
        return cursor.rowcount > 0

    # ---- Messages -------------------------------------------------------------
    def add_message(
        self,
        device_id: str,
        conversation_id: str,
        role: Role,
        content: str,
        tokens: int | None = None,
        elapsed_time: float | None = None,
        failed: bool = False,
    ) -> Message:
        message = Message(uuid.uuid4().hex, conversation_id, role, content, time.time(), tokens, elapsed_time, failed)
        with self._connect(device_id) as db:
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
