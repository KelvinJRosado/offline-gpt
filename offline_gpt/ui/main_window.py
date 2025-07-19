import os
import sys
import threading
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QToolBar, QLabel, QScrollArea, QSizePolicy, QFrame, QMessageBox, QListWidget, QListWidgetItem, QSplitter
)
from PySide6.QtCore import Qt, QDateTime, QTimer
from PySide6.QtGui import QAction
from offline_gpt.database.history import ChatHistoryDB
from offline_gpt.backend.llm import LLMBackend

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../models/Phi-3-mini-4k-instruct-q4.gguf')

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
        self.resize(800, 700)
        self.dark_mode = False
        db_path = os.path.join(os.path.expanduser("~"), ".offline_gpt_chat.db")
        self.history_db = ChatHistoryDB(db_path, storage_limit_mb=500)
        self.llm = None
        self._load_llm_backend()
        self.current_conversation_id = None
        self.sidebar_expanded = False
        self._init_ui()
        self._apply_theme()
        self._load_conversations()

    def _load_llm_backend(self):
        try:
            self.llm = LLMBackend(os.path.abspath(MODEL_PATH))
        except Exception as e:
            QMessageBox.critical(self, "LLM Load Error", f"Failed to load LLM model: {e}")
            self.llm = None

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar (minimized by default)
        self.sidebar = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar_layout.setSpacing(0)
        self.sidebar.setFixedWidth(40)
        self.sidebar_btn = QPushButton("☰")
        self.sidebar_btn.setFixedWidth(40)
        self.sidebar_btn.clicked.connect(self.toggle_sidebar)
        self.sidebar_layout.addWidget(self.sidebar_btn)
        self.convo_list = QListWidget()
        self.convo_list.setVisible(False)
        self.convo_list.itemClicked.connect(self.select_conversation)
        self.sidebar_layout.addWidget(self.convo_list)
        self.new_convo_btn = QPushButton("+")
        self.new_convo_btn.setVisible(False)
        self.new_convo_btn.clicked.connect(self.create_conversation)
        self.sidebar_layout.addWidget(self.new_convo_btn)
        main_layout.addWidget(self.sidebar)

        # Main chat area
        self.chat_area = QWidget()
        chat_layout = QVBoxLayout(self.chat_area)
        chat_layout.setContentsMargins(6, 6, 6, 6)
        chat_layout.setSpacing(6)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.addStretch(1)
        self.scroll_area.setWidget(self.chat_container)
        chat_layout.addWidget(self.scroll_area)

        input_layout = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type your message...")
        self.input_box.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_box)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        chat_layout.addLayout(input_layout)

        toolbar = QToolBar()
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        self.theme_action = QAction("Toggle Dark/Light Mode", self)
        self.theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(self.theme_action)
        self.clear_action = QAction("Clear Chat", self)
        self.clear_action.triggered.connect(self.clear_chat)
        toolbar.addAction(self.clear_action)

        main_layout.addWidget(self.chat_area)

    def toggle_sidebar(self):
        self.sidebar_expanded = not self.sidebar_expanded
        if self.sidebar_expanded:
            self.sidebar.setFixedWidth(220)
            self.convo_list.setVisible(True)
            self.new_convo_btn.setVisible(True)
        else:
            self.sidebar.setFixedWidth(40)
            self.convo_list.setVisible(False)
            self.new_convo_btn.setVisible(False)

    def _load_conversations(self):
        self.convo_list.clear()
        conversations = self.history_db.get_conversations()
        for convo_id, summary in conversations:
            item = QListWidgetItem(summary)
            item.setData(Qt.ItemDataRole.UserRole, convo_id)
            self.convo_list.addItem(item)
        # Auto-select the first conversation if none selected
        if conversations and not self.current_conversation_id:
            self.current_conversation_id = conversations[0][0]
            self._load_history()

    def select_conversation(self, item):
        convo_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_conversation_id = convo_id
        self._load_history()
        self.toggle_sidebar()

    def create_conversation(self):
        summary = "New Conversation"
        convo_id = self.history_db.create_conversation(summary)
        self.current_conversation_id = convo_id
        self._load_conversations()
        self._load_history()
        self.toggle_sidebar()

    def _load_history(self):
        # Clear UI
        for i in reversed(range(self.chat_layout.count() - 1)):
            widget = self.chat_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        if not self.current_conversation_id:
            return
        history = self.history_db.get_history(self.current_conversation_id)
        parent_width = self.scroll_area.viewport().width()
        for row in history:
            _id, _convo_id, timestamp, user_msg, llm_resp = row
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
        if not user_msg or not self.current_conversation_id:
            return
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        parent_width = self.scroll_area.viewport().width()
        self.add_chat_bubble("You", user_msg, is_user=True, timestamp=timestamp, parent_width=parent_width)
        self.input_box.clear()
        # Call LLM in a background thread
        threading.Thread(target=self._get_llm_and_display, args=(user_msg, timestamp, parent_width), daemon=True).start()

    def _get_llm_and_display(self, user_msg, timestamp, parent_width):
        if not self.llm:
            llm_response = "[LLM not available]"
        else:
            llm_response = self.llm.chat(user_msg)
        def update_ui():
            self.add_chat_bubble("LLM", llm_response, is_user=False, timestamp=timestamp, parent_width=parent_width)
            if self.current_conversation_id:
                self.history_db.add_message(self.current_conversation_id, user_msg, llm_response)
            # Check storage limit
            if os.path.exists(self.history_db.db_path):
                size_mb = os.path.getsize(self.history_db.db_path) / (1024 * 1024)
                if size_mb > self.history_db.storage_limit_mb:
                    QMessageBox.warning(self, "Storage Limit Reached", "Chat history storage limit reached. Please delete old chats to free up space.")
        QTimer.singleShot(0, update_ui)

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

    def clear_chat(self):
        if not self.current_conversation_id:
            return
        reply = QMessageBox.question(
            self,
            "Clear Chat",
            "Are you sure you want to clear the current chat history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history_db.clear_history(self.current_conversation_id)
            for i in reversed(range(self.chat_layout.count() - 1)):
                widget = self.chat_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            self._scroll_to_bottom()

def run_app():
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec()) 