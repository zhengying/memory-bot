"""
Abstract base class for LLM providers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Iterator, Optional
from .models import Message, LLMResponse


class LLMProvider(ABC):
    """Abstract base class for LLM providers

    All LLM providers must implement these methods.
    This allows swapping providers without changing application code.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        **kwargs
    ):
        """Initialize LLM provider

        Args:
            api_key: API key for the provider
            model: Model name to use
            **kwargs: Additional provider-specific parameters
        """
        self.api_key = api_key
        self.model = model
        self.kwargs = kwargs

    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        **kwargs
    ) -> LLMResponse:
        """Send chat completion request

        Args:
            messages: List of messages to send
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            LLMResponse with content and metadata
        """
        pass

    @abstractmethod
    def chat_stream(
        self,
        messages: List[Message],
        **kwargs
    ) -> Iterator[str]:
        """Stream chat completion

        Args:
            messages: List of messages to send
            **kwargs: Additional parameters

        Yields:
            Response chunks as they arrive
        """
        pass

    @abstractmethod
    def count_tokens(self, messages: List[Message]) -> int:
        """Count tokens in messages

        Args:
            messages: List of messages to count

        Returns:
            Number of tokens
        """
        pass

    def estimate_cost(self, messages: List[Message]) -> float:
        """Estimate cost of processing messages

        This is a rough estimate; actual cost may vary.

        Args:
            messages: List of messages to process

        Returns:
            Estimated cost in USD (may be 0 if not implemented)
        """
        tokens = self.count_tokens(messages)
        # Default: assume $0.001 per 1K tokens
        return (tokens / 1000) * 0.001
