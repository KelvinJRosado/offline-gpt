import sqlite3
import os

class ChatHistoryDB:
    def __init__(self, db_path: str, storage_limit_mb: int):
        self.db_path = db_path
        self.storage_limit_mb = storage_limit_mb
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_message TEXT,
                    llm_response TEXT
                )
            ''')
            conn.commit()

    def add_message(self, user_message: str, llm_response: str):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO chat_history (user_message, llm_response) VALUES (?, ?)', (user_message, llm_response))
            conn.commit()
        self._enforce_storage_limit()

    def get_history(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM chat_history ORDER BY timestamp ASC')
            return c.fetchall()

    def delete_message(self, message_id: int):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM chat_history WHERE id = ?', (message_id,))
            conn.commit()

    def _enforce_storage_limit(self):
        if os.path.exists(self.db_path):
            size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
            if size_mb > self.storage_limit_mb:
                # TODO: Implement logic to require user to delete old chats
                pass 