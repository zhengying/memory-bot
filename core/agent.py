"""
Agent Engine - Core orchestrator integrating all components
"""
from typing import Dict, Any, Optional, List
from core.llm import LLMProvider, Message
from core.memory import MemoryDatabase
from core.session import SessionManager, ContextBuilder, ContextConfig, Session


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
        llm_provider: LLMProvider,
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
