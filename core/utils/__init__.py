"""
Token counter utility using tiktoken for accurate token counting
"""
from typing import List, Optional
import tiktoken
from core.llm import Message


class TokenCounter:
    """Accurate token counter using tiktoken
    
    Supports multiple encodings for different models:
    - cl100k_base: GPT-4, GPT-3.5-turbo
    - p50k_base: GPT-3 (davinci, curie)
    - r50k_base: GPT-2
    """
    
    def __init__(self, model: str = "gpt-4"):
        """Initialize token counter
        
        Args:
            model: Model name to determine encoding
        """
        self.model = model
        self.encoding = self._get_encoding(model)
    
    def _get_encoding(self, model: str) -> tiktoken.Encoding:
        """Get appropriate encoding for model
        
        Args:
            model: Model name
            
        Returns:
            Tiktoken encoding
        """
        # Map common model names to encodings
        model_lower = model.lower()
        
        if "gpt-4" in model_lower or "gpt-3.5-turbo" in model_lower:
            return tiktoken.get_encoding("cl100k_base")
        elif "davinci" in model_lower or "curie" in model_lower:
            return tiktoken.get_encoding("p50k_base")
        elif "gpt-2" in model_lower:
            return tiktoken.get_encoding("r50k_base")
        else:
            # Default to cl100k_base for modern models
            return tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text
        
        Args:
            text: Text to count
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        return len(self.encoding.encode(text))
    
    def count_message(self, message: Message) -> int:
        """Count tokens in a message
        
        Includes overhead for message structure (role, content, etc.)
        
        Args:
            message: Message to count
            
        Returns:
            Number of tokens
        """
        # Every message follows <|start|>{role/name}\n{content}<|end|>\n
        # Base tokens per message
        tokens = 3  # <|start|>, \n, <|end|>
        
        # Role tokens
        tokens += self.count_tokens(message.role)
        
        # Content tokens
        tokens += self.count_tokens(message.content)
        
        return tokens
    
    def count_messages(self, messages: List[Message]) -> int:
        """Count tokens in a list of messages
        
        Args:
            messages: List of messages
            
        Returns:
            Total number of tokens
        """
        if not messages:
            return 0
        
        total = 0
        for message in messages:
            total += self.count_message(message)
        
        # Every reply is primed with <|start|>assistant<|end|>
        total += 3
        
        return total
    
    def estimate_cost(self, messages: List[Message], 
                     input_cost_per_1k: float = 0.01,
                     output_cost_per_1k: float = 0.03) -> dict:
        """Estimate cost for processing messages
        
        Args:
            messages: Messages to process
            input_cost_per_1k: Cost per 1K input tokens
            output_cost_per_1k: Cost per 1K output tokens
            
        Returns:
            Dict with token count and cost estimates
        """
        tokens = self.count_messages(messages)
        input_cost = (tokens / 1000) * input_cost_per_1k
        
        return {
            "input_tokens": tokens,
            "estimated_input_cost": input_cost,
            "estimated_output_tokens": tokens,  # Assume similar length
            "estimated_output_cost": (tokens / 1000) * output_cost_per_1k,
            "total_estimated_cost": input_cost + ((tokens / 1000) * output_cost_per_1k)
        }


# Global token counter instance
_default_counter: Optional[TokenCounter] = None


def get_token_counter(model: str = "gpt-4") -> TokenCounter:
    """Get token counter instance
    
    Args:
        model: Model name
        
    Returns:
        TokenCounter instance
    """
    global _default_counter
    if _default_counter is None:
        _default_counter = TokenCounter(model)
    return _default_counter


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text (convenience function)
    
    Args:
        text: Text to count
        model: Model name
        
    Returns:
        Number of tokens
    """
    counter = get_token_counter(model)
    return counter.count_tokens(text)


def count_messages(messages: List[Message], model: str = "gpt-4") -> int:
    """Count tokens in messages (convenience function)
    
    Args:
        messages: Messages to count
        model: Model name
        
    Returns:
        Total number of tokens
    """
    counter = get_token_counter(model)
    return counter.count_messages(messages)
