import os
import sys
import threading
import logging
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QToolBar, QLabel, QScrollArea, QSizePolicy, QFrame, QMessageBox, QListWidget, QListWidgetItem, QSplitter, QMenu
)
from PySide6.QtCore import Qt, QDateTime, QTimer, Signal, QObject
from PySide6.QtGui import QAction
from offline_gpt.database.history import ChatHistoryDB
from offline_gpt.backend.llm import LLMBackend

# Setup structured logging
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'app.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("offline-gpt")

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../models/Phi-3-mini-4k-instruct-q4.gguf')

class LoadingBubble(QWidget):
    def __init__(self, parent_width=600):
        super().__init__()
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(5, 3, 5, 3)  # Reduced margins
        outer_layout.setSpacing(2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        sender_label = QLabel("LLM")
        sender_label.setStyleSheet("font-weight: bold; color: #444;")
        outer_layout.addWidget(sender_label, alignment=Qt.AlignmentFlag.AlignLeft)

        # Message row with loading dots
        msg_row = QHBoxLayout()
        msg_row.setContentsMargins(0, 0, 0, 0)  # No margins in message row
        loading_label = QLabel("Thinking")
        loading_label.setWordWrap(True)
        loading_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        # Match the chat bubble width - 98% of parent width
        bubble_width = int(parent_width * 0.98)
        loading_label.setMaximumWidth(bubble_width)
        loading_label.setMinimumWidth(250)
        loading_label.setStyleSheet("background: #f1f1f1; border-radius: 10px; padding: 12px; color: #222; font-size: 14px;")
        msg_row.addWidget(loading_label)
        msg_row.addStretch(1)
        outer_layout.addLayout(msg_row)

        # Add animated dots
        self.dots_label = QLabel("...")
        self.dots_label.setStyleSheet("font-size: 16px; color: #888;")
        outer_layout.addWidget(self.dots_label, alignment=Qt.AlignmentFlag.AlignLeft)

        ts_label = QLabel(QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"))
        ts_label.setStyleSheet("font-size: 10px; color: #888;")
        outer_layout.addWidget(ts_label, alignment=Qt.AlignmentFlag.AlignLeft)

        # Add a bottom border for separation
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        outer_layout.addWidget(line)

        # Start dot animation
        self.dot_count = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate_dots)
        self.timer.start(500)  # Update every 500ms

    def _animate_dots(self):
        self.dot_count = (self.dot_count + 1) % 4
        self.dots_label.setText("." * self.dot_count)

    def stop_animation(self):
        self.timer.stop()

class ChatBubble(QWidget):
    def __init__(self, sender, message, timestamp, is_user=False, parent_width=600):
        super().__init__()
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(5, 3, 5, 3)  # Reduced margins
        outer_layout.setSpacing(2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        sender_label = QLabel(sender)
        sender_label.setStyleSheet("font-weight: bold; color: #0078d7;" if is_user else "font-weight: bold; color: #444;")
        outer_layout.addWidget(sender_label, alignment=Qt.AlignmentFlag.AlignRight if is_user else Qt.AlignmentFlag.AlignLeft)

        # Message row with stretch for alignment
        msg_row = QHBoxLayout()
        msg_row.setContentsMargins(0, 0, 0, 0)  # No margins in message row
        if is_user:
            msg_row.addStretch(1)
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        # Increase bubble width to 98% of parent width for maximum text display
        bubble_width = int(parent_width * 0.98)
        msg_label.setMaximumWidth(bubble_width)
        msg_label.setMinimumWidth(250)  # Increased minimum width further
        msg_label.setStyleSheet(
            "background: #e1f5fe; border-radius: 10px; padding: 12px; color: #222; font-size: 14px;" if is_user else
            "background: #f1f1f1; border-radius: 10px; padding: 12px; color: #222; font-size: 14px;"
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
    # Signal to handle LLM response in main thread
    llm_response_ready = Signal(str, str, str, int)  # llm_response, user_msg, timestamp, parent_width
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
        # Auto-focus the input field
        self.input_box.setFocus()
        
        # Connect the signal to the slot
        self.llm_response_ready.connect(self._handle_llm_response)
        
        logger.info("App started and UI initialized.")

    def _load_llm_backend(self):
        try:
            self.llm = LLMBackend(os.path.abspath(MODEL_PATH))
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
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
        # Hamburger button at the top
        self.sidebar_btn = QPushButton("☰")
        self.sidebar_btn.setFixedWidth(40)
        self.sidebar_btn.setFixedHeight(40)
        self.sidebar_btn.clicked.connect(self.toggle_sidebar)
        self.sidebar_layout.addWidget(self.sidebar_btn, alignment=Qt.AlignmentFlag.AlignTop)
        self.convo_list = QListWidget()
        self.convo_list.setVisible(False)
        self.convo_list.itemClicked.connect(self.select_conversation)
        self.convo_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.convo_list.customContextMenuRequested.connect(self.show_conversation_context_menu)
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
        self.input_box.setFocus()  # Auto-focus input field

    def create_conversation(self):
        summary = "New Conversation"
        convo_id = self.history_db.create_conversation(summary)
        self.current_conversation_id = convo_id
        self._load_conversations()
        self._load_history()
        self.toggle_sidebar()
        self.input_box.setFocus() # Auto-focus input field

    def _update_conversation_summary(self, user_msg):
        """Update conversation summary based on the first user message"""
        if not self.current_conversation_id:
            return
        
        # Generate a 2-5 word summary from the first message
        words = user_msg.split()[:5]  # Take first 5 words
        summary = " ".join(words)
        if len(summary) > 30:  # Truncate if too long
            summary = summary[:27] + "..."
        
        # Update the conversation summary in the database
        self.history_db.update_conversation_summary(self.current_conversation_id, summary)
        
        # Refresh the conversation list
        self._load_conversations()

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
        
        # Update conversation summary on first message
        if self.chat_layout.count() == 2:  # Only user message + stretch widget
            self._update_conversation_summary(user_msg)
        
        # Add loading bubble
        self.loading_bubble = LoadingBubble(parent_width)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, self.loading_bubble)
        self._scroll_to_bottom()
        
        # Call LLM in a background thread
        threading.Thread(target=self._get_llm_and_display, args=(user_msg, timestamp, parent_width), daemon=True).start()

    def _get_llm_and_display(self, user_msg, timestamp, parent_width):
        if not self.llm:
            llm_response = "[LLM not available]"
        else:
            llm_response = self.llm.chat(user_msg)
        
        logger.info(f"LLM thread completed, emitting signal with response: {llm_response[:50]}...")
        
        # Emit signal to update UI in main thread
        self.llm_response_ready.emit(llm_response, user_msg, timestamp, parent_width)

    def _handle_llm_response(self, llm_response, user_msg, timestamp, parent_width):
        """Handle LLM response in the main thread"""
        logger.info(f"Signal received, adding LLM response to UI: {llm_response[:100]}...")
        
        # Remove loading bubble
        if hasattr(self, 'loading_bubble') and self.loading_bubble:
            self.loading_bubble.stop_animation()
            self.loading_bubble.setParent(None)
            self.loading_bubble = None
        
        # Add the actual response
        self.add_chat_bubble("LLM", llm_response, is_user=False, timestamp=timestamp, parent_width=parent_width)
        if self.current_conversation_id:
            self.history_db.add_message(self.current_conversation_id, user_msg, llm_response)
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
        logger.info(f"Creating chat bubble for {sender}: {message[:50]}...")
        bubble = ChatBubble(sender, message, timestamp, is_user, parent_width)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self._scroll_to_bottom()
        logger.info(f"Chat bubble added, total bubbles: {self.chat_layout.count() - 1}")

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
            logger.info(f"Clearing chat for conversation {self.current_conversation_id}")
            self.history_db.clear_history(self.current_conversation_id)
            # Clear chat bubbles from UI
            for i in reversed(range(self.chat_layout.count() - 1)):
                widget = self.chat_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            self._scroll_to_bottom()
            # Remove conversation from list
            for i in range(self.convo_list.count()):
                item = self.convo_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == self.current_conversation_id:
                    self.convo_list.takeItem(i)
                    break

    def show_conversation_context_menu(self, position):
        """Show context menu for conversation list"""
        item = self.convo_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        delete_action = menu.addAction("Delete Conversation")
        delete_action.triggered.connect(lambda: self.delete_conversation(item))
        
        # Show menu at cursor position
        menu.exec(self.convo_list.mapToGlobal(position))

    def delete_conversation(self, item):
        """Delete a conversation from the list and database"""
        convo_id = item.data(Qt.ItemDataRole.UserRole)
        summary = item.text()
        
        reply = QMessageBox.question(
            self,
            "Delete Conversation",
            f"Are you sure you want to delete '{summary}'? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info(f"Deleting conversation {convo_id}: {summary}")
            
            # Delete from database
            self.history_db.delete_conversation(convo_id)
            
            # Remove from list
            self.convo_list.takeItem(self.convo_list.row(item))
            
            # If this was the current conversation, clear the chat area
            if convo_id == self.current_conversation_id:
                self.current_conversation_id = None
                # Clear chat bubbles from UI
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