import os
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QToolBar, QLabel, QScrollArea, QSizePolicy, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QAction
from offline_gpt.database.history import ChatHistoryDB

class ChatBubble(QWidget):
    def __init__(self, sender, message, timestamp, is_user=False, parent_width=600):
        super().__init__()
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 5, 10, 5)
        outer_layout.setSpacing(2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        sender_label = QLabel(sender)
        sender_label.setStyleSheet("font-weight: bold; color: #0078d7;" if is_user else "font-weight: bold; color: #444;")
        outer_layout.addWidget(sender_label, alignment=Qt.AlignmentFlag.AlignRight if is_user else Qt.AlignmentFlag.AlignLeft)

        # Message row with stretch for alignment
        msg_row = QHBoxLayout()
        if is_user:
            msg_row.addStretch(1)
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bubble_width = int(parent_width * 0.7)
        msg_label.setMaximumWidth(bubble_width)
        msg_label.setMinimumWidth(80)
        msg_label.setStyleSheet(
            "background: #e1f5fe; border-radius: 10px; padding: 8px; color: #222;" if is_user else
            "background: #f1f1f1; border-radius: 10px; padding: 8px; color: #222;"
        )
        msg_row.addWidget(msg_label)
        if not is_user:
            msg_row.addStretch(1)
        outer_layout.addLayout(msg_row)

        ts_label = QLabel(timestamp)
        ts_label.setStyleSheet("font-size: 10px; color: #888;")
        outer_layout.addWidget(ts_label, alignment=Qt.AlignmentFlag.AlignRight if is_user else Qt.AlignmentFlag.AlignLeft)

        # Add a bottom border for separation
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        outer_layout.addWidget(line)

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Offline-GPT")
        self.resize(600, 700)
        self._init_ui()
        self.dark_mode = False
        self._apply_theme()
        # Chat history DB setup
        db_path = os.path.join(os.path.expanduser("~"), ".offline_gpt_chat.db")
        self.history_db = ChatHistoryDB(db_path, storage_limit_mb=500)
        self._load_history()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # Scrollable chat area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.addStretch(1)
        self.scroll_area.setWidget(self.chat_container)
        main_layout.addWidget(self.scroll_area)

        # Input area
        input_layout = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type your message...")
        self.input_box.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_box)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        main_layout.addLayout(input_layout)

        # Toolbar for dark/light mode
        toolbar = QToolBar()
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        self.theme_action = QAction("Toggle Dark/Light Mode", self)
        self.theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(self.theme_action)

    def _load_history(self):
        history = self.history_db.get_history()
        parent_width = self.scroll_area.viewport().width()
        for row in history:
            _id, timestamp, user_msg, llm_resp = row
            if user_msg:
                self._add_bubble_from_history("You", user_msg, timestamp, True, parent_width)
            if llm_resp:
                self._add_bubble_from_history("LLM", llm_resp, timestamp, False, parent_width)
        self._scroll_to_bottom()

    def _add_bubble_from_history(self, sender, message, timestamp, is_user, parent_width):
        bubble = ChatBubble(sender, message, timestamp, is_user, parent_width)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

    def send_message(self):
        user_msg = self.input_box.text().strip()
        if not user_msg:
            return
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        parent_width = self.scroll_area.viewport().width()
        self.add_chat_bubble("You", user_msg, is_user=True, timestamp=timestamp, parent_width=parent_width)
        self.input_box.clear()
        # Placeholder for LLM response
        llm_response = self.get_llm_response(user_msg)
        self.add_chat_bubble("LLM", llm_response, is_user=False, timestamp=timestamp, parent_width=parent_width)
        # Save to DB
        self.history_db.add_message(user_msg, llm_response)
        # Check storage limit
        if os.path.exists(self.history_db.db_path):
            size_mb = os.path.getsize(self.history_db.db_path) / (1024 * 1024)
            if size_mb > self.history_db.storage_limit_mb:
                QMessageBox.warning(self, "Storage Limit Reached", "Chat history storage limit reached. Please delete old chats to free up space.")

    def add_chat_bubble(self, sender, message, is_user=False, timestamp=None, parent_width=None):
        if timestamp is None:
            timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        if parent_width is None:
            parent_width = self.scroll_area.viewport().width()
        bubble = ChatBubble(sender, message, timestamp, is_user, parent_width)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def get_llm_response(self, user_msg):
        # TODO: Integrate with backend.llm.LLMBackend
        return "[LLM response placeholder]"

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self._apply_theme()

    def _apply_theme(self):
        if self.dark_mode:
            self.setStyleSheet("""
                QMainWindow { background: #232629; }
                QLineEdit { background: #2b2b2b; color: #f0f0f0; }
                QPushButton { background: #444; color: #fff; }
                QLabel { color: #f0f0f0; }
                QScrollArea { background: #232629; }
            """)
        else:
            self.setStyleSheet("")

def run_app():
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec()) 