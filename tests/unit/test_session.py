"""
Unit tests for Session module
"""
import pytest
import tempfile
import os
from core.llm import Message, MockLLMProvider
from core.memory import MemoryDatabase, MemoryEntry, SearchQuery
from core.session import (
    Session,
    ContextConfig,
    BuiltContext,
    SessionManager,
    ContextBuilder
)


class TestSession:
    """Test Session dataclass"""

    def test_create_session(self):
        """Test creating a session"""
        session = Session(id="test-123")

        assert session.id == "test-123"
        assert len(session.messages) == 0

    def test_add_message(self):
        """Test adding messages"""
        session = Session(id="test")

        session.add_message(Message(role="user", content="Hello"))
        session.add_message(Message(role="assistant", content="Hi"))

        assert len(session.messages) == 2
        assert session.messages[0].role == "user"

    def test_last_n_messages(self):
        """Test getting last n messages"""
        session = Session(id="test")

        for i in range(10):
            session.add_message(Message(role="user", content=f"Message {i}"))

        last_3 = session.last_n_messages(3)

        assert len(last_3) == 3
        assert last_3[0].content == "Message 7"

    def test_total_tokens(self):
        """Test total token count with tiktoken"""
        session = Session(id="test")
        from core.utils import count_messages

        session.add_message(Message(role="user", content="Hello world"))

        # Should use tiktoken for accurate counting (not character length)
        expected_tokens = count_messages(session.messages)
        assert session.total_tokens() == expected_tokens
        # "Hello world" is 2 tokens, plus message overhead
        assert session.total_tokens() < len("Hello world") * 2  # Much less than char count


class TestContextConfig:
    """Test ContextConfig"""

    def test_default_config(self):
        """Test default configuration"""
        config = ContextConfig()

        assert config.max_tokens == 8000
        assert config.system_prompt == "You are a helpful assistant."

    def test_custom_config(self):
        """Test custom configuration"""
        config = ContextConfig(
            max_tokens=4000,
            system_prompt="You are a coding assistant."
        )

        assert config.max_tokens == 4000


class TestBuiltContext:
    """Test BuiltContext"""

    def test_build_context(self):
        """Test building context"""
        context = BuiltContext(
            messages=[
                Message(role="system", content="Helpful"),
                Message(role="user", content="Hello")
            ],
            token_count=100
        )

        assert len(context.messages) == 2
        assert context.token_count == 100


class TestSessionManager:
    """Test SessionManager"""

    def test_create_session(self):
        """Test creating session"""
        manager = SessionManager()

        session = manager.create_session()

        assert session.id is not None
        assert len(manager.sessions) == 1

    def test_create_session_with_id(self):
        """Test creating session with custom ID"""
        manager = SessionManager()

        session = manager.create_session(session_id="custom-123")

        assert session.id == "custom-123"

    def test_get_session(self):
        """Test getting session"""
        manager = SessionManager()

        created = manager.create_session(session_id="test-123")
        retrieved = manager.get_session("test-123")

        assert retrieved is not None
        assert retrieved.id == "test-123"

    def test_delete_session(self):
        """Test deleting session"""
        manager = SessionManager()

        manager.create_session(session_id="test-123")
        deleted = manager.delete_session("test-123")

        assert deleted is True

    def test_list_sessions(self):
        """Test listing sessions"""
        manager = SessionManager()

        manager.create_session(session_id="s1")
        manager.create_session(session_id="s2")

        sessions = manager.list_sessions()

        assert len(sessions) == 2

    def test_add_message(self):
        """Test adding message to session"""
        manager = SessionManager()

        session = manager.create_session(session_id="test")
        manager.add_message("test", Message(role="user", content="Hello"))

        assert len(session.messages) == 1


class TestContextBuilder:
    """Test ContextBuilder"""

    def test_build_context_basic(self):
        """Test building basic context"""
        llm = MockLLMProvider(api_key="test", model="gpt-4")
        builder = ContextBuilder(llm_provider=llm)

        session = Session(id="test")
        session.add_message(Message(role="user", content="Hello"))

        context = builder.build(session)

        assert len(context.messages) > 0
        assert not context.truncated

    def test_build_context_with_memory(self):
        """Test building context with memory database"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name

        try:
            db = MemoryDatabase(db_path)
            db.connect()
            db.create_schema()

            # Add test memory
            db.insert(MemoryEntry(
                id=None,
                source_file="test.md",
                section="Python Notes",
                content="Python is a great programming language."
            ))

            llm = MockLLMProvider(api_key="test", model="gpt-4")
            builder = ContextBuilder(llm_provider=llm, memory_db=db)

            session = Session(id="test")
            session.add_message(Message(role="user", content="Tell me about programming"))

            # Use a search term that should match
            context = builder.build(session, query="programming")

            # Context should be built without errors
            assert isinstance(context.memory_results, list)
            assert len(context.messages) > 0

            db.close()
        finally:
            os.unlink(db_path)

    def test_build_context_truncated(self):
        """Test context truncation"""
        config = ContextConfig(max_tokens=100)
        llm = MockLLMProvider(api_key="test", model="gpt-4")
        builder = ContextBuilder(llm_provider=llm, config=config)

        session = Session(id="test")

        # Add long messages
        for i in range(10):
            session.add_message(Message(
                role="user",
                content="x" * 100
            ))

        context = builder.build(session)

        assert context.truncated is True
