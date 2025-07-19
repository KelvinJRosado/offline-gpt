"""
Test suite for Offline-GPT application.

This module contains unit tests for the various components of the application.
"""

import pytest
import os
import tempfile
from offline_gpt.database.history import ChatHistoryDB
from offline_gpt.backend.llm import LLMBackend


class TestChatHistoryDB:
    """Test cases for the ChatHistoryDB class."""
    
    def setup_method(self):
        """Set up test database."""
        self.temp_db_path = tempfile.mktemp(suffix='.db')
        self.db = ChatHistoryDB(self.temp_db_path, storage_limit_mb=10)
    
    def teardown_method(self):
        """Clean up test database."""
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)
    
    def test_create_conversation(self):
        """Test creating a new conversation."""
        convo_id = self.db.create_conversation("Test Conversation")
        assert convo_id is not None
        assert len(convo_id) > 0
        
        conversations = self.db.get_conversations()
        assert len(conversations) == 1
        assert conversations[0][1] == "Test Conversation"
    
    def test_add_message(self):
        """Test adding messages to a conversation."""
        convo_id = self.db.create_conversation("Test Conversation")
        self.db.add_message(convo_id, "Hello", "Hi there!")
        
        history = self.db.get_history(convo_id)
        assert len(history) == 1
        assert history[0][3] == "Hello"  # user_message
        assert history[0][4] == "Hi there!"  # llm_response
    
    def test_delete_conversation(self):
        """Test deleting a conversation."""
        convo_id = self.db.create_conversation("Test Conversation")
        self.db.add_message(convo_id, "Hello", "Hi there!")
        
        # Verify conversation exists
        conversations = self.db.get_conversations()
        assert len(conversations) == 1
        
        # Delete conversation
        self.db.delete_conversation(convo_id)
        
        # Verify conversation is deleted
        conversations = self.db.get_conversations()
        assert len(conversations) == 0


class TestLLMBackend:
    """Test cases for the LLMBackend class."""
    
    def test_model_path_validation(self):
        """Test that invalid model paths raise appropriate errors."""
        with pytest.raises(FileNotFoundError):
            LLMBackend("/nonexistent/model.gguf")
    
    # Note: Full LLM testing would require a test model file
    # This is a placeholder for when we have a test model


def test_dummy():
    """Dummy test to ensure pytest is working."""
    assert True 