"""
Agent Engine - Core orchestrator integrating all components
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from core.llm import LLMProvider, Message
from core.memory import MemoryDatabase, MemoryEntry, SearchQuery
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
        
        Extracts and stores valuable information from conversation:
        1. User preferences and facts
        2. Important context for future reference
        3. Avoids storing generic conversational content
        
        Args:
            session: Current session
            user_message: User's message
            assistant_response: Assistant's response
        """
        if not self.memory:
            return
        
        # Extract user facts from message
        memory_entries = self._extract_memories(session, user_message, assistant_response)
        
        # Store each extracted memory
        for entry in memory_entries:
            self.memory.insert(entry)
    
    def _extract_memories(
        self,
        session: Session,
        user_message: str,
        assistant_response: str
    ) -> List[MemoryEntry]:
        """Extract memory entries from conversation
        
        Uses simple heuristics to identify valuable information:
        - User preferences (喜欢、讨厌、偏好等)
        - Personal facts (我是、我在、我的等)
        - Context worth remembering
        
        Args:
            session: Current session
            user_message: User's message
            assistant_response: Assistant's response
            
        Returns:
            List of memory entries to store
        """
        entries = []
        
        # Keywords indicating personal information
        personal_keywords = [
            "我", "我的", "我喜欢", "我讨厌", "我是", "我在",
            "i like", "i love", "i hate", "i am", "i'm", "my ",
            "my name is", "i work", "i live", "i prefer", "i want",
            "name is", "work as", "live in", "prefer", "favorite",
        ]
        
        # Check if user message contains personal information
        user_lower = user_message.lower()
        has_personal_info = any(kw.lower() in user_lower for kw in personal_keywords)
        
        if has_personal_info and len(user_message) > 10:
            # Create memory entry for user fact
            entry = MemoryEntry(
                id=None,
                source_file=f"session_{session.id}",
                section="User Fact",
                content=user_message,
                tags=["user_fact", "auto_extracted"],
                metadata={
                    "session_id": session.id,
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                    "type": "user_preference"
                }
            )
            entries.append(entry)
        
        # Store important assistant responses (educational, factual)
        # Only if response is substantial and informative
        if len(assistant_response) > 100 and len(assistant_response) < 2000:
            # Check if it's an informative response (not just conversational)
            informative_markers = [
                "是", "可以", "需要", "方法", "步骤", "解释",
                "is", "can", "should", "method", "steps", "how to",
                "because", "therefore", "example", "such as"
            ]
            
            is_informative = any(marker in assistant_response.lower() 
                               for marker in informative_markers)
            
            if is_informative:
                # Check for duplicates by searching similar content
                similar = self.memory.search(
                    SearchQuery(
                        query=assistant_response[:50],
                        limit=1
                    )
                )
                
                # Only store if no very similar content exists
                if not similar or similar[0].score > -1.0:  # bm25 score, higher is worse
                    entry = MemoryEntry(
                        id=None,
                        source_file=f"session_{session.id}",
                        section="Knowledge",
                        content=assistant_response,
                        tags=["knowledge", "auto_extracted"],
                        metadata={
                            "session_id": session.id,
                            "extracted_at": datetime.now(timezone.utc).isoformat(),
                            "type": "assistant_response",
                            "query": user_message[:100]
                        }
                    )
                    entries.append(entry)
        
        return entries
    
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
