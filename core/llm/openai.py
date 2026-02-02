"""
OpenAI Provider implementation for LLM
"""
import os
from typing import Iterator, List, Optional
from openai import OpenAI
from .base import LLMProvider
from .models import Message, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI API provider
    
    Supports OpenAI-compatible APIs including:
    - OpenAI official API
    - Volcengine (火山引擎)
    - Other OpenAI-compatible services
    """
    
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """Initialize OpenAI provider
        
        Args:
            api_key: API key
            model: Model name (e.g., 'gpt-4', 'ark-code-latest')
            base_url: Optional base URL for OpenAI-compatible API
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        """
        super().__init__(api_key, model, **kwargs)
        
        # Initialize OpenAI client
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        
        self.client = OpenAI(**client_kwargs)
    
    def chat(
        self,
        messages: List[Message],
        **kwargs
    ) -> LLMResponse:
        """Send chat completion request
        
        Args:
            messages: List of messages
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse with content and metadata
        """
        # Convert messages to OpenAI format
        openai_messages = [msg.to_dict() for msg in messages]
        
        # Merge default kwargs with provided kwargs
        request_kwargs = {**self.kwargs, **kwargs}
        
        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            **request_kwargs
        )
        
        # Extract response data
        choice = response.choices[0]
        
        return LLMResponse(
            content=choice.message.content,
            model=self.model,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            finish_reason=choice.finish_reason,
            metadata={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            }
        )
    
    def chat_stream(
        self,
        messages: List[Message],
        **kwargs
    ) -> Iterator[str]:
        """Stream chat completion
        
        Args:
            messages: List of messages
            **kwargs: Additional parameters
            
        Yields:
            Response chunks as they arrive
        """
        # Convert messages to OpenAI format
        openai_messages = [msg.to_dict() for msg in messages]
        
        # Merge default kwargs with provided kwargs
        request_kwargs = {**self.kwargs, **kwargs}
        
        # Call OpenAI API with streaming
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            stream=True,
            **request_kwargs
        )
        
        # Yield chunks as they arrive
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    
    def count_tokens(self, messages: List[Message]) -> int:
        """Count tokens in messages
        
        Note: This is a rough estimate. For accurate counts, use tiktoken.
        
        Args:
            messages: List of messages
            
        Returns:
            Estimated token count
        """
        # Rough estimate: 4 characters per token
        total_chars = sum(len(msg.content) for msg in messages)
        return total_chars // 4


def create_volcengine_provider(
    api_key: str,
    model: str = "ark-code-latest",
    **kwargs
) -> OpenAIProvider:
    """Create a Volcengine (火山引擎) provider
    
    Args:
        api_key: Volcengine API key
        model: Model name (default: ark-code-latest)
        **kwargs: Additional parameters
        
    Returns:
        OpenAIProvider configured for Volcengine
    """
    return OpenAIProvider(
        api_key=api_key,
        model=model,
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        **kwargs
    )
