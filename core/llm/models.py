"""
Data models for LLM interactions
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class Message:
    """LLM message

    Attributes:
        role: Message role ('system', 'user', 'assistant')
        content: Message content
        metadata: Optional metadata for tracking/analysis
    """
    role: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        """Convert to dict format for LLM API"""
        return {"role": self.role, "content": self.content}

    def __str__(self) -> str:
        return f"{self.role}: {self.content[:50]}{'...' if len(self.content) > 50 else ''}"


@dataclass
class LLMResponse:
    """LLM response

    Attributes:
        content: Response content
        model: Model name used
        tokens_used: Total tokens consumed
        finish_reason: Why the response finished ('stop', 'length', 'content_filter', etc.)
        metadata: Optional metadata (request_id, latency, etc.)
    """
    content: str
    model: str
    tokens_used: int = 0
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"LLMResponse(model={self.model}, tokens={self.tokens_used})"
