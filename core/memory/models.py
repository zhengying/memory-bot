"""
Data models for memory system
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class MemoryEntry:
    """Memory entry from database

    Attributes:
        id: Unique identifier
        source_file: Source markdown file path
        section: Section/heading
        content: Content text
        tags: List of tags
        metadata: Additional metadata
        created_at: Timestamp
        updated_at: Timestamp
    """
    id: Optional[int]
    source_file: str
    section: str
    content: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __str__(self) -> str:
        return f"MemoryEntry(id={self.id}, section='{self.section}', content='{self.content[:50]}...')"


@dataclass
class SearchQuery:
    """Search query for memory

    Attributes:
        query: Search text
        limit: Maximum results
        source_file: Filter by source file
        tags: Filter by tags
    """
    query: str
    limit: int = 10
    source_file: Optional[str] = None
    tags: Optional[List[str]] = None


@dataclass
class SearchResult:
    """Search result

    Attributes:
        entry: Memory entry
        score: Relevance score
        snippet: Text snippet with highlights
    """
    entry: MemoryEntry
    score: float
    snippet: str

    def __str__(self) -> str:
        return f"SearchResult(score={self.score:.2f}, {self.entry})"
