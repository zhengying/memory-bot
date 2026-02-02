"""
Markdown file parser for memory extraction
"""
import os
from typing import List
from .models import MemoryEntry


class MarkdownParser:
    """Parse markdown files into memory entries

    Extracts:
    - Headings as sections
    - Content blocks
    - Empty sections are filtered out
    """

    def parse_file(self, file_path: str) -> List[MemoryEntry]:
        """Parse markdown file

        Args:
            file_path: Path to markdown file

        Returns:
            List of memory entries

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return self.parse_content(content, source_file=file_path)

    def parse_content(self, content: str, source_file: str = "") -> List[MemoryEntry]:
        """Parse markdown content

        Args:
            content: Markdown content
            source_file: Source file path

        Returns:
            List of memory entries
        """
        entries = []

        # Split into sections by headings
        lines = content.split('\n')

        current_section: str = ""
        current_content = []

        for line in lines:
            # Check for heading
            if line.startswith('#'):
                # Save previous section if exists
                if current_section and current_content:
                    entry_content = '\n'.join(current_content).strip()
                    if entry_content:  # Skip empty sections
                        entries.append(MemoryEntry(
                            id=None,
                            source_file=source_file,
                            section=current_section,
                            content=entry_content
                        ))

                # Start new section
                current_section = line.lstrip('#').strip()
                current_content = []
            else:
                current_content.append(line)

        # Don't forget last section
        if current_section and current_content:
            entry_content = '\n'.join(current_content).strip()
            if entry_content:
                entries.append(MemoryEntry(
                    id=None,
                    source_file=source_file,
                    section=current_section,
                    content=entry_content
                ))

        return entries
