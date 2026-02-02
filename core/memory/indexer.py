"""
Indexer for markdown files into memory database
"""
import os
from glob import glob
from typing import List
from .models import MemoryEntry
from .database import MemoryDatabase
from .parser import MarkdownParser


class MemoryIndexer:
    """Index markdown files into memory database

    Combines MarkdownParser and MemoryDatabase for easy indexing.
    """

    def __init__(self, db: MemoryDatabase):
        """Initialize indexer

        Args:
            db: Memory database instance
        """
        self.db = db
        self.parser = MarkdownParser()

    def index_file(self, file_path: str) -> List[int]:
        """Index a markdown file

        Args:
            file_path: Path to markdown file

        Returns:
            List of inserted entry IDs
        """
        # Parse file
        entries = self.parser.parse_file(file_path)

        # Insert into database
        inserted_ids = []
        for entry in entries:
            entry_id = self.db.insert(entry)
            inserted_ids.append(entry_id)

        return inserted_ids

    def index_directory(self, directory: str, pattern: str = "*.md") -> List[int]:
        """Index all markdown files in directory

        Args:
            directory: Path to directory
            pattern: File pattern (default: *.md)

        Returns:
            List of all inserted entry IDs
        """
        all_ids = []

        for file_path in glob(os.path.join(directory, pattern)):
            ids = self.index_file(file_path)
            all_ids.extend(ids)

        return all_ids

    def reindex(self, file_path: str) -> List[int]:
        """Re-index a file (clear old entries, add new)

        Args:
            file_path: Path to markdown file

        Returns:
            List of inserted entry IDs
        """
        # Clear old entries from this file
        if self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute("DELETE FROM memories WHERE source_file = ?", (file_path,))
            self.db.conn.commit()

        # Re-index
        return self.index_file(file_path)
