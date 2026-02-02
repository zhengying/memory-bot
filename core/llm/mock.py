"""
Mock LLM provider for testing and development
"""
from typing import List, Iterator, Optional
from .base import LLMProvider
from .models import Message, LLMResponse


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing

    This provider doesn't call any real API.
    It's useful for testing and offline development.
    """

    def __init__(
        self,
        api_key: str = "test-key",
        model: str = "gpt-4",
        response: Optional[str] = None,
        **kwargs
    ):
        """Initialize mock provider

        Args:
            api_key: Mock API key (not used)
            model: Model name to simulate
            response: Fixed response to return (default: "Mock response")
            **kwargs: Additional parameters (ignored)
        """
        super().__init__(api_key, model, **kwargs)
        self.mock_response = response or "Mock response"
        self.last_messages: Optional[List[Message]] = None
        self.call_count = 0

    def chat(
        self,
        messages: List[Message],
        **kwargs
    ) -> LLMResponse:
        """Mock chat completion

        Args:
            messages: List of messages
            **kwargs: Ignored

        Returns:
            Mock LLMResponse
        """
        self.last_messages = messages
        self.call_count += 1

        # Simple mock: count tokens as character length
        tokens = sum(len(m.content) for m in messages)

        return LLMResponse(
            content=self.mock_response,
            model=self.model,
            tokens_used=tokens,
            finish_reason="stop",
            metadata={"call_count": self.call_count}
        )

    def chat_stream(
        self,
        messages: List[Message],
        **kwargs
    ) -> Iterator[str]:
        """Mock streaming response

        Args:
            messages: List of messages
            **kwargs: Ignored

        Yields:
            Response chunks word by word
        """
        self.last_messages = messages
        self.call_count += 1

        # Stream word by word
        words = self.mock_response.split()
        for word in words:
            yield word + " "

    def count_tokens(self, messages: List[Message]) -> int:
        """Mock token counting (simplified)

        This is a rough approximation. For real applications,
        use tiktoken or provider-specific tokenizers.

        Args:
            messages: List of messages

        Returns:
            Approximate token count (character length)
        """
        return sum(len(m.content) for m in messages)

    def set_response(self, response: str):
        """Set a new mock response

        Args:
            response: New response to return
        """
        self.mock_response = response

    def reset(self):
        """Reset mock state"""
        self.call_count = 0
        self.last_messages = None
