"""
Unit tests for Memory module
"""
import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from core.memory import (
    MemoryEntry,
    SearchQuery,
    SearchResult,
    MemoryDatabase,
    MarkdownParser,
    MemoryIndexer
)


class TestMemoryEntry:
    """Test MemoryEntry dataclass"""

    def test_create_entry(self):
        """Test creating a memory entry"""
        entry = MemoryEntry(
            id=None,
            source_file="test.md",
            section="Introduction",
            content="This is test content"
        )

        assert entry.source_file == "test.md"
        assert entry.section == "Introduction"
        assert entry.content == "This is test content"

    def test_entry_with_tags(self):
        """Test entry with tags"""
        entry = MemoryEntry(
            id=1,
            source_file="test.md",
            section="Test",
            content="Content",
            tags=["important", "todo"]
        )

        assert "important" in entry.tags
        assert "todo" in entry.tags

    def test_entry_with_metadata(self):
        """Test entry with metadata"""
        entry = MemoryEntry(
            id=1,
            source_file="test.md",
            section="Test",
            content="Content",
            metadata={"priority": "high", "author": "test"}
        )

        assert entry.metadata["priority"] == "high"
        assert entry.metadata["author"] == "test"


class TestSearchQuery:
    """Test SearchQuery dataclass"""

    def test_create_query(self):
        """Test creating search query"""
        query = SearchQuery(query="test search")

        assert query.query == "test search"
        assert query.limit == 10

    def test_query_with_filters(self):
        """Test query with filters"""
        query = SearchQuery(
            query="test",
            limit=5,
            source_file="test.md",
            tags=["important"]
        )

        assert query.limit == 5
        assert query.source_file == "test.md"
        assert "important" in query.tags


class TestMemoryDatabase:
    """Test MemoryDatabase"""

    def test_create_and_connect(self):
        """Test creating and connecting to database"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name

        try:
            db = MemoryDatabase(db_path)
            db.connect()
            assert db.conn is not None
            db.close()
        finally:
            os.unlink(db_path)

    def test_create_schema(self):
        """Test creating database schema"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name

        try:
            db = MemoryDatabase(db_path)
            db.connect()
            db.create_schema()

            # Check tables exist
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ('memories', 'memories_fts')
            """)
            tables = [row[0] for row in cursor.fetchall()]

            assert 'memories' in tables
            assert 'memories_fts' in tables

            db.close()
        finally:
            os.unlink(db_path)

    def test_insert_entry(self):
        """Test inserting memory entry"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name

        try:
            db = MemoryDatabase(db_path)
            db.connect()
            db.create_schema()

            entry = MemoryEntry(
                id=None,
                source_file="test.md",
                section="Test Section",
                content="Test content",
                tags=["test"],
                metadata={"key": "value"}
            )

            entry_id = db.insert(entry)
            assert entry_id > 0

            db.close()
        finally:
            os.unlink(db_path)

    def test_search(self):
        """Test searching memories"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name

        try:
            db = MemoryDatabase(db_path)
            db.connect()
            db.create_schema()

            # Insert test entries
            db.insert(MemoryEntry(
                id=None,
                source_file="test.md",
                section="About Python",
                content="Python is a great programming language for data science."
            ))

            db.insert(MemoryEntry(
                id=None,
                source_file="test.md",
                section="About JavaScript",
                content="JavaScript is popular for web development."
            ))

            search_query = SearchQuery(query="programming")
            results = db.search(search_query)

            assert len(results) > 0
            assert "programming" in results[0].entry.content.lower()

            db.close()
        finally:
            os.unlink(db_path)

    def test_get_all(self):
        """Test getting all memories"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name

        try:
            db = MemoryDatabase(db_path)
            db.connect()
            db.create_schema()

            db.insert(MemoryEntry(
                id=None,
                source_file="test.md",
                section="Test 1",
                content="Content 1"
            ))

            db.insert(MemoryEntry(
                id=None,
                source_file="test.md",
                section="Test 2",
                content="Content 2"
            ))

            entries = db.get_all()

            assert len(entries) == 2

            db.close()
        finally:
            os.unlink(db_path)

    def test_clear(self):
        """Test clearing all memories"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name

        try:
            db = MemoryDatabase(db_path)
            db.connect()
            db.create_schema()

            db.insert(MemoryEntry(
                id=None,
                source_file="test.md",
                section="Test",
                content="Content"
            ))

            assert len(db.get_all()) == 1

            db.clear()
            assert len(db.get_all()) == 0

            db.close()
        finally:
            os.unlink(db_path)

    def test_count(self):
        """Test counting memories"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name

        try:
            db = MemoryDatabase(db_path)
            db.connect()
            db.create_schema()

            assert db.count() == 0

            db.insert(MemoryEntry(
                id=None,
                source_file="test.md",
                section="Test",
                content="Content"
            ))

            assert db.count() == 1

            db.close()
        finally:
            os.unlink(db_path)


class TestMarkdownParser:
    """Test MarkdownParser"""

    def test_parse_content_with_headings(self):
        """Test parsing markdown with headings"""
        parser = MarkdownParser()

        content = """
# Introduction

This is introduction content.

# Main Section

This is main section content.

## Subsection

This is a subsection.
"""

        entries = parser.parse_content(content, source_file="test.md")

        assert len(entries) == 3
        assert entries[0].section == "Introduction"
        assert entries[1].section == "Main Section"
        assert entries[2].section == "Subsection"

    def test_parse_empty_content(self):
        """Test parsing empty content"""
        parser = MarkdownParser()

        entries = parser.parse_content("", source_file="test.md")

        assert len(entries) == 0

    def test_parse_file(self):
        """Test parsing a markdown file"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            delete=False,
            encoding='utf-8'
        ) as tmp:
            tmp.write("""# Test Document

This is test content.

# Another Section

More content here.
""")
            tmp_path = tmp.name

        try:
            parser = MarkdownParser()
            entries = parser.parse_file(tmp_path)

            assert len(entries) == 2
            assert entries[0].section == "Test Document"
            assert entries[1].section == "Another Section"
        finally:
            os.unlink(tmp_path)


class TestMemoryIndexer:
    """Test MemoryIndexer"""

    def test_index_file(self):
        """Test indexing a markdown file"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            delete=False,
            encoding='utf-8'
        ) as tmp:
            tmp.write("""# Python Notes

Python is a great language.

# JavaScript Notes

JavaScript is for web.
""")
            tmp_path = tmp.name

        with tempfile.NamedTemporaryFile(delete=False) as db_tmp:
            db_path = db_tmp.name

        try:
            db = MemoryDatabase(db_path)
            db.connect()
            db.create_schema()

            indexer = MemoryIndexer(db)
            entry_ids = indexer.index_file(tmp_path)

            assert len(entry_ids) == 2
            assert all(id > 0 for id in entry_ids)

            entries = db.get_all()
            assert len(entries) == 2

            db.close()
        finally:
            os.unlink(tmp_path)
            os.unlink(db_path)

    def test_index_and_search(self):
        """Test indexing and searching"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            delete=False,
            encoding='utf-8'
        ) as tmp:
            tmp.write("""# Data Science

Data science uses Python for analysis.

# Web Development

Web development uses JavaScript for frontend.
""")
            tmp_path = tmp.name

        with tempfile.NamedTemporaryFile(delete=False) as db_tmp:
            db_path = db_tmp.name

        try:
            db = MemoryDatabase(db_path)
            db.connect()
            db.create_schema()

            indexer = MemoryIndexer(db)
            indexer.index_file(tmp_path)

            # Search for "Python"
            results = db.search(SearchQuery(query="Python"))

            assert len(results) > 0
            assert "Python" in results[0].entry.content

            db.close()
        finally:
            os.unlink(tmp_path)
            os.unlink(db_path)

    def test_index_directory(self):
        """Test indexing a directory of markdown files"""
        tmpdir = tempfile.mkdtemp()

        try:
            # Create test files - each with 2 sections
            (Path(tmpdir) / "file1.md").write_text("""# File 1 Section 1

Content from file 1 section 1.

# File 1 Section 2

Content from file 1 section 2.
""")

            (Path(tmpdir) / "file2.md").write_text("""# File 2 Section 1

Content from file 2 section 1.

# File 2 Section 2

Content from file 2 section 2.
""")

            with tempfile.NamedTemporaryFile(delete=False) as db_tmp:
                db_path = db_tmp.name

            try:
                db = MemoryDatabase(db_path)
                db.connect()
                db.create_schema()

                indexer = MemoryIndexer(db)
                entry_ids = indexer.index_directory(tmpdir)

                assert len(entry_ids) == 4  # 2 files x 2 sections each

                db.close()
            finally:
                os.unlink(db_path)
        finally:
            # Clean up temp directory
            for f in Path(tmpdir).glob("*"):
                f.unlink()
            os.rmdir(tmpdir)
