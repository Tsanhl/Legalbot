"""Conversation Store (SQLite). Persists sessions, messages and user feedback.

Swap for Redis (TTL) or Postgres later; the interface is the four public methods
the orchestrator uses: create_session / history / add_message / add_feedback.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY, title TEXT, created REAL, updated REAL
);
CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY, session_id TEXT, role TEXT, content TEXT,
  meta TEXT, created REAL
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created);
CREATE TABLE IF NOT EXISTS feedback (
  id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT, rating INTEGER,
  category TEXT, comment TEXT, created REAL
);
"""


class ConversationStore:
    def __init__(self, db_path: Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(db_path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._db.executescript(SCHEMA)
            cols = {r[1] for r in self._db.execute("PRAGMA table_info(sessions)")}
            if "user_id" not in cols:   # per-user history (older single-user chats belong to "local")
                self._db.execute("ALTER TABLE sessions ADD COLUMN user_id TEXT DEFAULT 'local'")
                self._db.execute("UPDATE sessions SET user_id='local' WHERE user_id IS NULL")
            self._db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, updated)")
            self._db.commit()

    # ---- sessions ----
    def create_session(self, title: str = "New chat", user_id: str = "local") -> str:
        sid = uuid.uuid4().hex[:12]
        now = time.time()
        with self._lock:
            self._db.execute("INSERT INTO sessions (id, title, created, updated, user_id) VALUES (?,?,?,?,?)",
                             (sid, title, now, now, user_id))
            self._db.commit()
        return sid

    def owns(self, sid: str, user_id: str) -> bool:
        return bool(self._db.execute("SELECT 1 FROM sessions WHERE id=? AND user_id=?", (sid, user_id)).fetchone())

    def ensure_session(self, sid: str | None, first_message: str = "", user_id: str = "local") -> str:
        if sid and self.owns(sid, user_id):
            return sid
        return self.create_session((first_message or "New chat")[:60], user_id)

    def list_sessions(self, user_id: str = "local") -> list[dict]:
        rows = self._db.execute("SELECT * FROM sessions WHERE user_id=? ORDER BY updated DESC LIMIT 200",
                                (user_id,)).fetchall()
        return [dict(r) for r in rows]

    def session_ids(self, user_id: str) -> set[str]:
        return {r[0] for r in self._db.execute("SELECT id FROM sessions WHERE user_id=?", (user_id,))}

    def rename_session(self, sid: str, title: str, user_id: str = "local") -> None:
        with self._lock:
            self._db.execute("UPDATE sessions SET title=? WHERE id=? AND user_id=?", (title[:80], sid, user_id))
            self._db.commit()

    def delete_session(self, sid: str, user_id: str = "local") -> None:
        if not self.owns(sid, user_id):
            return
        with self._lock:
            self._db.execute("DELETE FROM messages WHERE session_id=?", (sid,))
            self._db.execute("DELETE FROM sessions WHERE id=?", (sid,))
            self._db.commit()

    # ---- messages ----
    def add_message(self, sid: str, role: str, content: str, meta: dict | None = None) -> str:
        mid = uuid.uuid4().hex[:12]
        now = time.time()
        with self._lock:
            self._db.execute(
                "INSERT INTO messages VALUES (?,?,?,?,?,?)",
                (mid, sid, role, content, json.dumps(meta or {}), now),
            )
            self._db.execute("UPDATE sessions SET updated=? WHERE id=?", (now, sid))
            self._db.commit()
        return mid

    def messages(self, sid: str) -> list[dict]:
        rows = self._db.execute(
            "SELECT * FROM messages WHERE session_id=? ORDER BY created", (sid,)
        ).fetchall()
        return [{**dict(r), "meta": json.loads(r["meta"] or "{}")} for r in rows]

    def history(self, sid: str, window_turns: int) -> list[dict]:
        """Sliding window: last N user+assistant pairs, oldest first."""
        rows = self._db.execute(
            "SELECT role, content FROM messages WHERE session_id=? ORDER BY created DESC LIMIT ?",
            (sid, window_turns * 2),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def get_message(self, mid: str) -> dict | None:
        r = self._db.execute("SELECT * FROM messages WHERE id=?", (mid,)).fetchone()
        return {**dict(r), "meta": json.loads(r["meta"] or "{}")} if r else None

    # ---- feedback ----
    def add_feedback(self, mid: str, sid: str, rating: int, category: str = "", comment: str = "") -> str:
        fid = uuid.uuid4().hex[:12]
        with self._lock:
            self._db.execute(
                "INSERT INTO feedback VALUES (?,?,?,?,?,?,?)",
                (fid, mid, sid, rating, category, comment, time.time()),
            )
            self._db.commit()
        return fid
