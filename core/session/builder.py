"""
Context builder for LLM from session and memory
"""
from typing import List, Optional
from .models import ContextConfig, BuiltContext, Session
from core.llm import LLMProvider, Message
from core.memory import MemoryDatabase, SearchQuery, SearchResult
from core.utils import count_messages


class ContextBuilder:
    """Build context from session and memory

    Combines:
    - System prompt
    - Memory search results
    - Message history
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        memory_db: Optional[MemoryDatabase] = None,
        config: Optional[ContextConfig] = None
    ):
        """Initialize context builder

        Args:
            llm_provider: LLM provider for token counting
            memory_db: Memory database (optional)
            config: Context configuration
        """
        self.llm = llm_provider
        self.memory = memory_db
        self.config = config or ContextConfig()

    def build(
        self,
        session: Session,
        query: Optional[str] = None
    ) -> BuiltContext:
        """Build context for LLM

        Args:
            session: Chat session
            query: Optional query for memory search

        Returns:
            Built context
        """
        messages = []
        memory_results = []

        # Add system prompt
        if self.config.system_prompt:
            messages.append(Message(
                role="system",
                content=self.config.system_prompt
            ))

        # Search memory if available and query provided
        if self.memory and query:
            search_results = self.memory.search(SearchQuery(
                query=query,
                limit=self.config.memory_max_results
            ))

            # Filter by relevance score
            for result in search_results:
                if result.score >= self.config.memory_min_score:
                    memory_results.append(result)

            # Add memory context
            if memory_results:
                memory_context = self._format_memory_results(memory_results)
                messages.append(Message(
                    role="system",
                    content=f"Relevant information:\n{memory_context}"
                ))

        # Add message history
        messages.extend(session.messages)

        # Count tokens accurately using tiktoken
        token_count: int = count_messages(messages)

        # Check if exceeds budget
        truncated = token_count > self.config.max_tokens

        if truncated:
            # Truncate messages using token-based strategy
            messages, token_count = self._truncate_to_budget(messages)
            truncated = True

        return BuiltContext(
            messages=messages,
            token_count=token_count,
            memory_results=memory_results,
            truncated=truncated
        )

    def _format_memory_results(self, results: List[SearchResult]) -> str:
        """Format memory results

        Args:
            results: Search results

        Returns:
            Formatted text
        """
        lines = []
        for i, result in enumerate(results, 1):
            entry = result.entry
            lines.append(f"{i}. [{entry.section}]")
            lines.append(f"   {result.snippet}")
            lines.append("")
        return "\n".join(lines)

    def _truncate_to_budget(self, messages: List[Message]) -> tuple[List[Message], int]:
        """Truncate messages to fit within token budget

        Uses a sliding window strategy:
        1. Always keep system messages (first 1-2 messages)
        2. Keep as many recent messages as possible within budget
        3. Remove middle/old messages if necessary

        Args:
            messages: Messages to truncate

        Returns:
            Tuple of (truncated messages, token count)
        """
        if not messages:
            return [], 0
        
        # Separate system messages from conversation
        system_messages = []
        conversation = []
        
        for i, msg in enumerate(messages):
            if msg.role == "system" and i < 2:  # Keep first 1-2 system messages
                system_messages.append(msg)
            else:
                conversation.append(msg)
        
        # Calculate system message tokens
        system_tokens = count_messages(system_messages)
        available_budget = self.config.max_tokens - system_tokens
        
        # If no budget left, just return system messages
        if available_budget <= 0:
            return system_messages, system_tokens
        
        # Try to fit as many recent conversation messages as possible
        # Start from the most recent and work backwards
        kept_conversation = []
        current_tokens = 0
        
        for msg in reversed(conversation):
            msg_tokens = count_messages([msg])
            
            if current_tokens + msg_tokens <= available_budget:
                kept_conversation.insert(0, msg)  # Insert at beginning to maintain order
                current_tokens += msg_tokens
            else:
                # Can't fit this message, stop here
                break
        
        # Combine system messages with kept conversation
        truncated = system_messages + kept_conversation
        total_tokens = count_messages(truncated)
        
        return truncated, total_tokens

    def _truncate_messages(self, messages: List[Message]) -> List[Message]:
        """Legacy truncate method for backward compatibility

        Args:
            messages: Messages to truncate

        Returns:
            Truncated messages
        """
        # Delegate to the new token-based method
        truncated, _ = self._truncate_to_budget(messages)
        return truncated
