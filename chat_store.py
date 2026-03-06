"""
Chat Store - Conversation & Message Persistence
=================================================
Stores chat conversations and messages in a separate SQLite database.
"""

import sqlite3
import uuid
import json
from datetime import datetime
from config import BASE_DIR
import os

CHAT_DB_PATH = os.path.join(BASE_DIR, "chat_history.db")


class ChatStore:
    """Manages conversation storage in SQLite."""

    def __init__(self, db_path=CHAT_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL DEFAULT 'Cuộc hội thoại mới',
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id              TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role            TEXT NOT NULL,
                content         TEXT NOT NULL,
                sql_query       TEXT,
                sql_data        TEXT,
                sql_columns     TEXT,
                row_count       INTEGER DEFAULT 0,
                created_at      TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conv 
            ON messages(conversation_id, created_at);
        """)
        conn.commit()
        conn.close()

    # ── Conversations ────────────────────────────────────

    def create_conversation(self, title=None):
        """Create a new conversation. Returns the conversation dict."""
        conv_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        title = title or "Cuộc hội thoại mới"

        conn = self._get_conn()
        conn.execute(
            "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (conv_id, title, now, now),
        )
        conn.commit()
        conn.close()
        return {"id": conv_id, "title": title, "created_at": now, "updated_at": now}

    def list_conversations(self):
        """List all conversations, newest first."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_conversation(self, conv_id):
        """Get a single conversation by ID."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?",
            (conv_id,),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def rename_conversation(self, conv_id, new_title):
        """Rename a conversation."""
        now = datetime.now().isoformat()
        conn = self._get_conn()
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (new_title, now, conv_id),
        )
        conn.commit()
        conn.close()

    def delete_conversation(self, conv_id):
        """Delete a conversation and all its messages."""
        conn = self._get_conn()
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
        conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        conn.commit()
        conn.close()

    # ── Messages ─────────────────────────────────────────

    def add_message(self, conversation_id, role, content,
                    sql_query=None, sql_data=None, sql_columns=None, row_count=0):
        """Add a message to a conversation."""
        msg_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # Serialize lists/dicts to JSON strings
        sql_data_json = json.dumps(sql_data) if sql_data is not None else None
        sql_columns_json = json.dumps(sql_columns) if sql_columns is not None else None

        conn = self._get_conn()
        conn.execute(
            """INSERT INTO messages 
               (id, conversation_id, role, content, sql_query, sql_data, sql_columns, row_count, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (msg_id, conversation_id, role, content,
             sql_query, sql_data_json, sql_columns_json, row_count, now),
        )
        # Update conversation's updated_at
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )
        conn.commit()
        conn.close()
        return msg_id

    def get_messages(self, conversation_id):
        """Get all messages for a conversation, ordered by time."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT id, role, content, sql_query, sql_data, sql_columns, row_count, created_at
               FROM messages WHERE conversation_id = ? ORDER BY created_at ASC""",
            (conversation_id,),
        ).fetchall()
        conn.close()

        messages = []
        for r in rows:
            msg = dict(r)
            # Deserialize JSON strings
            if msg["sql_data"]:
                msg["sql_data"] = json.loads(msg["sql_data"])
            if msg["sql_columns"]:
                msg["sql_columns"] = json.loads(msg["sql_columns"])
            messages.append(msg)
        return messages

    def get_history_for_llm(self, conversation_id, max_pairs=20):
        """
        Get conversation history formatted for OpenAI messages array.
        Returns the last `max_pairs` user/assistant pairs (~max_pairs*2 messages).
        """
        all_msgs = self.get_messages(conversation_id)

        # Build simple role/content pairs for LLM
        history = []
        for msg in all_msgs:
            history.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Limit to last max_pairs*2 messages
        max_messages = max_pairs * 2
        if len(history) > max_messages:
            history = history[-max_messages:]

        return history

    def auto_title(self, conversation_id, first_question):
        """Auto-generate a title from the first question."""
        title = first_question[:50]
        if len(first_question) > 50:
            title += "..."
        self.rename_conversation(conversation_id, title)
