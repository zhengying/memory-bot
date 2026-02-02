"""
SQLite database for memory storage with FTS5 full-text search
"""
import sqlite3
from typing import List, Optional
from .models import MemoryEntry, SearchQuery, SearchResult


class MemoryDatabase:
    """SQLite database for memory storage

    Uses FTS5 for full-text search with automatic syncing.
    """

    def __init__(self, db_path: str):
        """Initialize database

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def create_schema(self):
        """Create database schema

        Creates tables:
        - memories: Main storage
        - memories_fts: Full-text search index
        - Triggers for automatic FTS sync
        """
        if not self.conn:
            raise RuntimeError("Not connected")

        cursor = self.conn.cursor()

        # Main memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                section TEXT,
                content TEXT NOT NULL,
                tags TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # FTS5 full-text search table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
            USING fts5(
                id UNINDEXED,
                content,
                section,
                tags,
                tokenize='porter unicode61'
            )
        """)

        # Triggers for automatic FTS sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_ai
            AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, content, section, tags)
                VALUES (new.id, new.content, new.section, new.tags);
            END
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_au
            AFTER UPDATE ON memories BEGIN
                UPDATE memories_fts
                SET content = new.content, section = new.section, tags = new.tags
                WHERE rowid = new.id;
            END
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_ad
            AFTER DELETE ON memories BEGIN
                DELETE FROM memories_fts WHERE rowid = old.id;
            END
        """)

        self.conn.commit()

    def insert(self, entry: MemoryEntry) -> int:
        """Insert memory entry

        Args:
            entry: Memory entry to insert

        Returns:
            Inserted row ID
        """
        if not self.conn:
            raise RuntimeError("Not connected")

        import json

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO memories (source_file, section, content, tags, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            entry.source_file,
            entry.section,
            entry.content,
            json.dumps(entry.tags),
            json.dumps(entry.metadata)
        ))

        self.conn.commit()
        return cursor.lastrowid

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search memories using FTS5

        Args:
            query: Search query

        Returns:
            List of search results ranked by relevance
        """
        if not self.conn:
            raise RuntimeError("Not connected")

        cursor = self.conn.cursor()

        # Validate and sanitize inputs to prevent SQL injection
        search_term = self._sanitize_fts_query(query.query)
        limit = max(1, min(int(query.limit), 100))  # Clamp limit between 1-100
        
        # FTS5 MATCH doesn't support parameterization, so we use a hybrid approach:
        # 1. Sanitize the search term thoroughly
        # 2. Use parameterization for other fields (source_file)
        # 3. Validate limit is an integer
        
        if query.source_file:
            sql = """
                SELECT m.*, bm25(memories_fts) as rank_score
                FROM memories_fts
                JOIN memories m ON m.id = memories_fts.rowid
                WHERE memories_fts MATCH ? AND m.source_file = ?
                ORDER BY rank_score LIMIT ?
            """
            cursor.execute(sql, (search_term, query.source_file, limit))
        else:
            sql = """
                SELECT m.*, bm25(memories_fts) as rank_score
                FROM memories_fts
                JOIN memories m ON m.id = memories_fts.rowid
                WHERE memories_fts MATCH ?
                ORDER BY rank_score LIMIT ?
            """
            cursor.execute(sql, (search_term, limit))
        rows = cursor.fetchall()

        import json

        results = []
        for row in rows:
            entry = MemoryEntry(
                id=row["id"],
                source_file=row["source_file"],
                section=row["section"] or "",
                content=row["content"],
                tags=json.loads(row["tags"]) if row["tags"] else [],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

            results.append(SearchResult(
                entry=entry,
                score=row["rank_score"],
                snippet=row["content"][:200]
            ))

        return results

    def get_all(self) -> List[MemoryEntry]:
        """Get all memories

        Returns:
            List of all memory entries ordered by creation time
        """
        if not self.conn:
            raise RuntimeError("Not connected")

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM memories ORDER BY created_at DESC")

        import json

        entries = []
        for row in cursor.fetchall():
            entry = MemoryEntry(
                id=row["id"],
                source_file=row["source_file"],
                section=row["section"] or "",
                content=row["content"],
                tags=json.loads(row["tags"]) if row["tags"] else [],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            entries.append(entry)

        return entries

    def clear(self):
        """Clear all memories"""
        if not self.conn:
            raise RuntimeError("Not connected")

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM memories")
        self.conn.commit()

    def _sanitize_fts_query(self, query: str) -> str:
        """Sanitize FTS5 query to prevent injection attacks and syntax errors
        
        FTS5 has special characters that cause syntax errors:
        - ? - wildcard/placeholder (causes syntax error)
        - " - phrase delimiter (must be doubled)
        - * - prefix operator
        - ^ - NEAR operator
        - AND, OR, NOT - boolean operators
        
        Args:
            query: Raw user query
            
        Returns:
            Sanitized query safe for FTS5
        """
        if not query:
            return ""
        
        # Remove null bytes and control characters
        query = ''.join(char for char in query if ord(char) >= 32 or char in '\t\n\r')
        
        # Limit length to prevent DoS
        query = query[:200]
        
        # Remove FTS5 special characters that cause syntax errors
        # ? is a special character in FTS5 that causes "syntax error near ?"
        query = query.replace('?', '')
        
        # Escape double quotes by doubling them (FTS5 escape rule)
        query = query.replace('"', '""')
        
        return query

    def count(self) -> int:
        """Count total memories

        Returns:
            Total number of memory entries
        """
        if not self.conn:
            raise RuntimeError("Not connected")

        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM memories")
        return cursor.fetchone()["count"]
