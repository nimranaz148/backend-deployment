# tests\test_chat_logging.py
"""
Property-based tests for chat logging functionality.

**Feature: hackathon-completion, Property 3: Chat Logging Completeness**
**Validates: Requirements 1.4**

For any completed chat interaction, a corresponding record SHALL exist in the 
Neon Postgres chat_history table with matching user_message and ai_response.
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock
import json

from src.services.db_service import DBService


class TestChatLoggingProperty:
    """Property tests for chat logging completeness."""
    
    @given(
        user_message=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        ai_response=st.text(min_size=1, max_size=2000).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100)
    def test_chat_logging_stores_messages(self, user_message: str, ai_response: str):
        """
        Property: For any user message and AI response, logging should store both.
        
        **Feature: hackathon-completion, Property 3: Chat Logging Completeness**
        **Validates: Requirements 1.4**
        """
        # Mock the database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('psycopg2.connect', return_value=mock_conn):
            db_service = DBService()
            db_service.conn = mock_conn
            
            # Log the interaction
            db_service.log_chat_interaction(
                user_message=user_message,
                ai_response=ai_response,
                source_documents=None
            )
            
            # Verify the INSERT was called with correct parameters
            mock_cursor.execute.assert_called()
            call_args = mock_cursor.execute.call_args
            
            # Check that user_message and ai_response are in the query parameters
            assert user_message in call_args[0][1], "User message should be logged"
            assert ai_response in call_args[0][1], "AI response should be logged"
    
    @given(
        user_message=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        ai_response=st.text(min_size=1, max_size=2000).filter(lambda x: x.strip()),
        source_docs=st.lists(
            st.fixed_dictionaries({
                'source_file': st.text(min_size=1, max_size=100),
                'score': st.floats(min_value=0, max_value=1),
                'text_snippet': st.text(min_size=1, max_size=200)
            }),
            min_size=0,
            max_size=5
        )
    )
    @settings(max_examples=100)
    def test_chat_logging_stores_source_documents(
        self, 
        user_message: str, 
        ai_response: str, 
        source_docs: list
    ):
        """
        Property: Source documents should be stored as JSON when provided.
        
        **Feature: hackathon-completion, Property 3: Chat Logging Completeness**
        **Validates: Requirements 1.4**
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('psycopg2.connect', return_value=mock_conn):
            db_service = DBService()
            db_service.conn = mock_conn
            
            db_service.log_chat_interaction(
                user_message=user_message,
                ai_response=ai_response,
                source_documents=source_docs if source_docs else None
            )
            
            mock_cursor.execute.assert_called()
            call_args = mock_cursor.execute.call_args
            
            # If source_docs provided, verify JSON serialization
            if source_docs:
                expected_json = json.dumps(source_docs)
                assert expected_json in call_args[0][1], "Source documents should be JSON serialized"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
