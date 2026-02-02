"""
Tests for session persistence
"""
import pytest
import tempfile
import os
from core.session import Session, SessionManager, SessionDatabase
from core.llm import Message


class TestSessionDatabase:
    """Test SessionDatabase persistence"""
    
    def test_create_database(self):
        """Test creating session database"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name
        
        try:
            db = SessionDatabase(db_path)
            db.connect()
            db.create_schema()
            
            # Should be able to count (returns 0 for empty db)
            assert db.count() == 0
            
            db.close()
        finally:
            os.unlink(db_path)
    
    def test_save_and_load_session(self):
        """Test saving and loading session"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Create and save session
            db = SessionDatabase(db_path)
            db.connect()
            db.create_schema()
            
            session = Session(id="test-123")
            session.add_message(Message(role="user", content="Hello"))
            session.add_message(Message(role="assistant", content="Hi there!"))
            
            db.save_session(session)
            
            # Verify saved
            assert db.count() == 1
            
            # Load session
            loaded = db.load_session("test-123")
            assert loaded is not None
            assert loaded.id == "test-123"
            assert len(loaded.messages) == 2
            assert loaded.messages[0].content == "Hello"
            
            db.close()
        finally:
            os.unlink(db_path)
    
    def test_delete_session(self):
        """Test deleting session"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name
        
        try:
            db = SessionDatabase(db_path)
            db.connect()
            db.create_schema()
            
            # Create and save session
            session = Session(id="test-123")
            db.save_session(session)
            assert db.count() == 1
            
            # Delete session
            deleted = db.delete_session("test-123")
            assert deleted is True
            assert db.count() == 0
            
            # Try to delete non-existent
            deleted = db.delete_session("nonexistent")
            assert deleted is False
            
            db.close()
        finally:
            os.unlink(db_path)
    
    def test_list_sessions(self):
        """Test listing sessions"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name
        
        try:
            db = SessionDatabase(db_path)
            db.connect()
            db.create_schema()
            
            # Create multiple sessions
            for i in range(3):
                session = Session(id=f"session-{i}")
                db.save_session(session)
            
            # List sessions
            sessions = db.list_sessions()
            assert len(sessions) == 3
            
            db.close()
        finally:
            os.unlink(db_path)


class TestSessionManagerPersistence:
    """Test SessionManager with persistence"""
    
    def test_session_manager_with_persistence(self):
        """Test session manager with database"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Create database
            db = SessionDatabase(db_path)
            db.connect()
            db.create_schema()
            
            # Create manager with database
            manager = SessionManager(db=db)
            
            # Create session
            session = manager.create_session()
            session.add_message(Message(role="user", content="Test message"))
            manager.persist_session(session.id)
            
            # Verify in memory
            assert session.id in manager.sessions
            
            # Create new manager (simulating restart)
            manager2 = SessionManager(db=db)
            
            # Should load session from database
            loaded = manager2.get_session(session.id)
            assert loaded is not None
            assert len(loaded.messages) == 1
            assert loaded.messages[0].content == "Test message"
            
            db.close()
        finally:
            os.unlink(db_path)
    
    def test_add_message_persistence(self):
        """Test that add_message persists to database"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name
        
        try:
            db = SessionDatabase(db_path)
            db.connect()
            db.create_schema()
            
            manager = SessionManager(db=db)
            
            # Create session
            session = manager.create_session(session_id="persist-test")
            
            # Add messages
            manager.add_message("persist-test", Message(role="user", content="Message 1"))
            manager.add_message("persist-test", Message(role="assistant", content="Response 1"))
            
            # Create new manager and load
            manager2 = SessionManager(db=db)
            loaded = manager2.get_session("persist-test")
            
            assert loaded is not None
            assert len(loaded.messages) == 2
            assert loaded.messages[1].role == "assistant"
            
            db.close()
        finally:
            os.unlink(db_path)
    
    def test_session_recovery_after_restart(self):
        """Test session recovery after simulated restart"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # First "process"
            db = SessionDatabase(db_path)
            db.connect()
            db.create_schema()
            
            manager1 = SessionManager(db=db)
            session = manager1.create_session(session_id="recovery-test")
            session.add_message(Message(role="user", content="Important conversation"))
            manager1.persist_session(session.id)
            
            # Close first process
            db.close()
            del manager1
            
            # Second "process" (restart)
            db2 = SessionDatabase(db_path)
            db2.connect()
            
            manager2 = SessionManager(db=db2)
            
            # Should recover the session
            recovered = manager2.get_session("recovery-test")
            assert recovered is not None
            assert len(recovered.messages) == 1
            assert recovered.messages[0].content == "Important conversation"
            
            db2.close()
        finally:
            os.unlink(db_path)
