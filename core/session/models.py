"""
Data models for session management
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from core.llm import Message


@dataclass
class Session:
    """Chat session

    Attributes:
        id: Unique session identifier
        messages: Message history
        created_at: Creation timestamp
        updated_at: Last update timestamp
        metadata: Additional metadata
    """
    id: str
    messages: List[Message] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: Message):
        """Add message to session

        Args:
            message: Message to add
        """
        self.messages.append(message)
        self.updated_at = datetime.now(timezone.utc)

    def last_n_messages(self, n: int) -> List[Message]:
        """Get last n messages

        Args:
            n: Number of messages

        Returns:
            Last n messages
        """
        return self.messages[-n:] if n > 0 else []

    def total_tokens(self, model: str = "gpt-4") -> int:
        """Count total tokens in session using tiktoken

        Args:
            model: Model name for token counting

        Returns:
            Accurate token count
        """
        try:
            from core.utils import count_messages
            return count_messages(self.messages, model)
        except ImportError:
            # Fallback to character-based estimate
            return sum(len(msg.content) for msg in self.messages)


@dataclass
class ContextConfig:
    """Configuration for context building

    Attributes:
        max_tokens: Maximum tokens for context
        system_prompt: System prompt
        memory_max_results: Max memory search results
        memory_min_score: Minimum relevance score
    """
    max_tokens: int = 8000
    system_prompt: str = "You are a helpful assistant."
    memory_max_results: int = 3
    memory_min_score: float = 0.0


@dataclass
class BuiltContext:
    """Built context from session and memory

    Attributes:
        messages: Complete message list for LLM
        token_count: Total token count
        memory_results: Memory entries used
        truncated: Whether context was truncated
    """
    messages: List[Message]
    token_count: int
    memory_results: List = field(default_factory=list)
    truncated: bool = False
