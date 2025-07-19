import sqlite3
import os
import uuid
from typing import Optional, List, Tuple

class ChatHistoryDB:
    def __init__(self, db_path: str, storage_limit_mb: int):
        self.db_path = db_path
        self.storage_limit_mb = storage_limit_mb
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            # Conversations table with UUIDs
            c.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    summary TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Chat history table with conversation_id as TEXT
            c.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_message TEXT,
                    llm_response TEXT,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            ''')
            conn.commit()

    # Conversation management
    def create_conversation(self, summary: str) -> str:
        conversation_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO conversations (id, summary) VALUES (?, ?)', (conversation_id, summary))
            conn.commit()
        return conversation_id

    def get_conversations(self) -> List[Tuple[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT id, summary FROM conversations ORDER BY created_at DESC')
            return c.fetchall()

    def update_conversation_summary(self, conversation_id: str, summary: str):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('UPDATE conversations SET summary = ? WHERE id = ?', (summary, conversation_id))
            conn.commit()

    def delete_conversation(self, conversation_id: str):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
            conn.commit()

    # Chat history management
    def add_message(self, conversation_id: str, user_message: str, llm_response: str):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO chat_history (conversation_id, user_message, llm_response) VALUES (?, ?, ?)', (conversation_id, user_message, llm_response))
            conn.commit()
        self._enforce_storage_limit()

    def get_history(self, conversation_id: str):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM chat_history WHERE conversation_id = ? ORDER BY timestamp ASC', (conversation_id,))
            return c.fetchall()

    def delete_message(self, message_id: int):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM chat_history WHERE id = ?', (message_id,))
            conn.commit()

    def clear_history(self, conversation_id: str):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM chat_history WHERE conversation_id = ?', (conversation_id,))
            conn.commit()

    def _enforce_storage_limit(self):
        if os.path.exists(self.db_path):
            size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
            if size_mb > self.storage_limit_mb:
                # TODO: Implement logic to require user to delete old chats
                pass 