"""
Unit tests for Agent module - The core engine integrating all components
"""
import pytest
import tempfile
import os
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch

from core.llm import Message, LLMResponse, MockLLMProvider
from core.memory import MemoryDatabase, MemoryEntry, SearchQuery
from core.session import Session, SessionManager, ContextBuilder, ContextConfig


# ============================
# Agent Engine
# ============================

class AgentEngine:
    """Core agent engine integrating LLM, Memory, and Session
    
    This is the main orchestrator that:
    1. Manages user sessions
    2. Retrieves relevant memories
    3. Builds context with memory + history
    4. Calls LLM and returns response
    5. Updates memory with new information
    """
    
    def __init__(
        self,
        llm_provider: MockLLMProvider,
        memory_db: Optional[MemoryDatabase] = None,
        session_manager: Optional[SessionManager] = None,
        config: Optional[ContextConfig] = None
    ):
        """Initialize agent engine
        
        Args:
            llm_provider: LLM provider for generating responses
            memory_db: Memory database for long-term memory
            session_manager: Session manager for chat sessions
            config: Context configuration
        """
        self.llm = llm_provider
        self.memory = memory_db
        self.sessions = session_manager or SessionManager()
        self.config = config or ContextConfig()
        self.context_builder = ContextBuilder(
            llm_provider=llm_provider,
            memory_db=memory_db,
            config=self.config
        )
    
    def chat(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        use_memory: bool = True
    ) -> Dict[str, Any]:
        """Process a chat message and return response
        
        Args:
            user_message: User's message
            session_id: Optional session ID (creates new if None)
            use_memory: Whether to use memory for context
            
        Returns:
            Response dict with content, session_id, and metadata
        """
        # Get or create session
        if session_id:
            session = self.sessions.get_session(session_id)
            if not session:
                session = self.sessions.create_session(session_id=session_id)
        else:
            session = self.sessions.create_session()
        
        # Add user message to session
        user_msg = Message(role="user", content=user_message)
        session.add_message(user_msg)
        
        # Build context with memory
        query = user_message if use_memory else None
        context = self.context_builder.build(session, query=query)
        
        # Call LLM
        llm_response = self.llm.chat(context.messages)
        
        # Add assistant response to session
        assistant_msg = Message(
            role="assistant",
            content=llm_response.content
        )
        session.add_message(assistant_msg)
        
        # Update memory if enabled
        if use_memory and self.memory:
            self._update_memory(session, user_message, llm_response.content)
        
        return {
            "content": llm_response.content,
            "session_id": session.id,
            "tokens_used": llm_response.tokens_used,
            "memory_used": len(context.memory_results) if context.memory_results else 0,
            "truncated": context.truncated
        }
    
    def _update_memory(
        self,
        session: Session,
        user_message: str,
        assistant_response: str
    ):
        """Update memory with new conversation
        
        In a real implementation, this would:
        1. Extract key information
        2. Summarize if needed
        3. Store in memory database
        
        For now, this is a placeholder.
        """
        # TODO: Implement memory extraction and storage
        pass
    
    def get_session_history(self, session_id: str) -> Optional[List[Message]]:
        """Get message history for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of messages or None if session not found
        """
        session = self.sessions.get_session(session_id)
        if session:
            return session.messages
        return None


# ============================
# Tests
# ============================

class TestAgentEngine:
    """Test AgentEngine"""
    
    def test_create_agent(self):
        """Test creating agent engine"""
        llm = MockLLMProvider(api_key="test", model="gpt-4")
        agent = AgentEngine(llm_provider=llm)
        
        assert agent.llm is llm
        assert agent.sessions is not None
        assert agent.context_builder is not None
    
    def test_chat_new_session(self):
        """Test chat creates new session"""
        llm = MockLLMProvider(api_key="test", model="gpt-4")
        agent = AgentEngine(llm_provider=llm)
        
        response = agent.chat("Hello")
        
        assert "content" in response
        assert "session_id" in response
        assert response["session_id"] is not None
    
    def test_chat_with_session(self):
        """Test chat with existing session"""
        llm = MockLLMProvider(api_key="test", model="gpt-4")
        agent = AgentEngine(llm_provider=llm)
        
        # First message
        response1 = agent.chat("Hello")
        session_id = response1["session_id"]
        
        # Second message with same session
        response2 = agent.chat("How are you?", session_id=session_id)
        
        assert response2["session_id"] == session_id
    
    def test_chat_with_memory(self):
        """Test chat with memory integration"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Setup memory
            db = MemoryDatabase(db_path)
            db.connect()
            db.create_schema()
            
            # Add memory
            db.insert(MemoryEntry(
                id=None,
                source_file="test.md",
                section="About Python",
                content="Python is a programming language"
            ))
            
            llm = MockLLMProvider(api_key="test", model="gpt-4")
            agent = AgentEngine(
                llm_provider=llm,
                memory_db=db
            )
            
            response = agent.chat(
                "What is Python?",
                use_memory=True
            )
            
            assert "content" in response
            assert "memory_used" in response
            
            db.close()
        finally:
            os.unlink(db_path)
    
    def test_chat_without_memory(self):
        """Test chat without memory"""
        llm = MockLLMProvider(api_key="test", model="gpt-4")
        agent = AgentEngine(llm_provider=llm)
        
        response = agent.chat("Hello", use_memory=False)
        
        assert response["memory_used"] == 0
    
    def test_get_session_history(self):
        """Test getting session history"""
        llm = MockLLMProvider(api_key="test", model="gpt-4")
        agent = AgentEngine(llm_provider=llm)
        
        # Create session with messages
        response = agent.chat("Hello")
        session_id = response["session_id"]
        
        # Get history
        history = agent.get_session_history(session_id)
        
        assert history is not None
        assert len(history) == 2  # user message + assistant response
    
    def test_get_nonexistent_session(self):
        """Test getting nonexistent session"""
        llm = MockLLMProvider(api_key="test", model="gpt-4")
        agent = AgentEngine(llm_provider=llm)
        
        history = agent.get_session_history("nonexistent")
        
        assert history is None
