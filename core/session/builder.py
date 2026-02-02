"""
Context builder for LLM from session and memory
"""
from typing import List, Optional
from .models import ContextConfig, BuiltContext, Session
from core.llm import LLMProvider, Message
from core.memory import MemoryDatabase, SearchQuery, SearchResult


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

        # Count tokens
        token_count: int = sum(len(msg.content) for msg in messages)

        # Check if exceeds budget
        truncated = token_count > self.config.max_tokens

        if truncated:
            # Truncate messages (simple strategy: keep system, drop history)
            messages = self._truncate_messages(messages)

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

    def _truncate_messages(self, messages: List[Message]) -> List[Message]:
        """Truncate messages to fit budget

        Args:
            messages: Messages to truncate

        Returns:
            Truncated messages
        """
        # Simple strategy: keep system messages, truncate history
        # Real implementation would use sliding window

        # Keep first 2 messages (usually system prompts)
        # Keep last 5 messages (recent conversation)
        if len(messages) > 7:
            return messages[:2] + messages[-5:]

        return messages
