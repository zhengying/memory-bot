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
from core.agent import AgentEngine

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
    
    def test_auto_memory_extraction(self):
        """Test automatic memory extraction from conversation"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Setup memory
            db = MemoryDatabase(db_path)
            db.connect()
            db.create_schema()
            
            llm = MockLLMProvider(api_key="test", model="gpt-4")
            agent = AgentEngine(
                llm_provider=llm,
                memory_db=db
            )
            
            # Set a longer response to trigger memory storage
            llm.set_response("Programming is the process of creating instructions for computers.")
            
            # Chat with personal information
            response = agent.chat(
                "My name is John and I like programming",
                use_memory=True
            )
            
            # Verify memory was stored
            all_memories = db.get_all()
            
            # Should have at least one memory (user fact)
            assert len(all_memories) >= 1
            
            # Check that user fact was stored
            user_facts = [m for m in all_memories if "user_fact" in m.tags]
            assert len(user_facts) >= 1
            
            db.close()
        finally:
            os.unlink(db_path)
