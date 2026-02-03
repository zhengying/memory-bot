"""Unit tests for FileTool."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from core.tools.file_tool import FileTool


class TestFileToolInit:
    """Test FileTool initialization."""

    def test_init_with_default_project_dir(self):
        """Test initialization with default project directory."""
        tool = FileTool()
        assert tool.name == "file"
        assert "file" in tool.description.lower()
        assert tool.project_dir is not None

    def test_init_with_custom_project_dir(self, tmp_path):
        """Test initialization with custom project directory."""
        tool = FileTool(project_dir=str(tmp_path))
        assert tool.project_dir == tmp_path.resolve()

    def test_init_with_str_path(self):
        """Test initialization with string path."""
        tool = FileTool(project_dir="/tmp")
        assert isinstance(tool.project_dir, Path)


class TestFileToolPathValidation:
    """Test path validation and security."""

    def test_is_path_safe_within_project(self, tmp_path):
        """Test that paths within project are safe."""
        tool = FileTool(project_dir=str(tmp_path))
        test_file = tmp_path / "test.txt"
        assert tool._is_path_safe(test_file) is True

    def test_is_path_safe_outside_project(self, tmp_path):
        """Test that paths outside project are unsafe."""
        tool = FileTool(project_dir=str(tmp_path))
        assert tool._is_path_safe("/etc/passwd") is False
        assert tool._is_path_safe("/root/.ssh/id_rsa") is False

    def test_is_path_safe_traversal_attack(self, tmp_path):
        """Test protection against directory traversal."""
        tool = FileTool(project_dir=str(tmp_path))
        malicious_path = tmp_path / ".." / ".." / "etc" / "passwd"
        assert tool._is_path_safe(malicious_path) is False

    def test_resolve_path_normalizes_path(self, tmp_path):
        """Test that resolve_path normalizes paths."""
        tool = FileTool(project_dir=str(tmp_path))
        result = tool._resolve_path("./test.txt")
        assert result == tmp_path / "test.txt"


class TestFileToolRead:
    """Test file reading operations."""

    def test_read_text_file(self, tmp_path):
        """Test reading a text file."""
        tool = FileTool(project_dir=str(tmp_path))
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        result = tool.read("test.txt")
        assert result.success is True
        assert result.data == "Hello, World!"

    def test_read_json_file(self, tmp_path):
        """Test reading a JSON file."""
        tool = FileTool(project_dir=str(tmp_path))
        test_file = tmp_path / "data.json"
        test_data = {"name": "test", "value": 42}
        test_file.write_text(json.dumps(test_data))

        result = tool.read("data.json")
        assert result.success is True
        assert result.data == test_data

    def test_read_missing_file(self, tmp_path):
        """Test reading a non-existent file."""
        tool = FileTool(project_dir=str(tmp_path))
        result = tool.read("nonexistent.txt")
        assert result.success is False
        assert "not found" in result.message.lower() or "does not exist" in result.message.lower()

    def test_read_unsafe_path(self, tmp_path):
        """Test reading from unsafe path."""
        tool = FileTool(project_dir=str(tmp_path))
        result = tool.read("/etc/passwd")
        assert result.success is False
        assert "access denied" in result.message.lower() or "outside" in result.message.lower()


class TestFileToolWrite:
    """Test file writing operations."""

    def test_write_new_file(self, tmp_path):
        """Test writing to a new file."""
        tool = FileTool(project_dir=str(tmp_path))
        result = tool.write("newfile.txt", "content")
        assert result.success is True
        assert (tmp_path / "newfile.txt").read_text() == "content"

    def test_write_overwrite_existing(self, tmp_path):
        """Test overwriting an existing file."""
        tool = FileTool(project_dir=str(tmp_path))
        (tmp_path / "existing.txt").write_text("old content")

        result = tool.write("existing.txt", "new content", mode="overwrite")
        assert result.success is True
        assert (tmp_path / "existing.txt").read_text() == "new content"

    def test_write_append_mode(self, tmp_path):
        """Test appending to a file."""
        tool = FileTool(project_dir=str(tmp_path))
        (tmp_path / "append.txt").write_text("first line\n")

        result = tool.write("append.txt", "second line\n", mode="append")
        assert result.success is True
        content = (tmp_path / "append.txt").read_text()
        assert "first line" in content
        assert "second line" in content

    def test_write_json_data(self, tmp_path):
        """Test writing JSON data."""
        tool = FileTool(project_dir=str(tmp_path))
        data = {"key": "value", "number": 42}

        result = tool.write("data.json", data)
        assert result.success is True

        written = json.loads((tmp_path / "data.json").read_text())
        assert written == data

    def test_write_unsafe_path(self, tmp_path):
        """Test writing to unsafe path."""
        tool = FileTool(project_dir=str(tmp_path))
        result = tool.write("/etc/malicious.txt", "content")
        assert result.success is False
        assert "access denied" in result.message.lower() or "outside" in result.message.lower()


class TestFileToolList:
    """Test file listing operations."""

    def test_list_empty_directory(self, tmp_path):
        """Test listing an empty directory."""
        tool = FileTool(project_dir=str(tmp_path))
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = tool.list("empty")
        assert result.success is True
        assert result.data == []

    def test_list_with_files(self, tmp_path):
        """Test listing files in directory."""
        tool = FileTool(project_dir=str(tmp_path))
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.txt").write_text("content2")

        result = tool.list("testdir")
        assert result.success is True
        files = [item["name"] for item in result.data]
        assert "file1.txt" in files
        assert "file2.txt" in files

    def test_list_recursive(self, tmp_path):
        """Test recursive directory listing."""
        tool = FileTool(project_dir=str(tmp_path))
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested content")

        result = tool.list(".", recursive=True)
        assert result.success is True
        # Should contain the nested file
        all_files = []
        for item in result.data:
            all_files.append(item["name"])
            if "children" in item:
                all_files.extend([c["name"] for c in item["children"]])
        assert "nested.txt" in all_files or "subdir" in all_files


class TestFileToolSearch:
    """Test file search operations."""

    def test_search_by_name(self, tmp_path):
        """Test searching files by name pattern."""
        tool = FileTool(project_dir=str(tmp_path))
        (tmp_path / "test1.txt").write_text("content")
        (tmp_path / "test2.py").write_text("content")
        (tmp_path / "other.log").write_text("content")

        result = tool.search("test*")
        assert result.success is True
        found = [item["name"] for item in result.data]
        assert "test1.txt" in found
        assert "test2.py" in found
        assert "other.log" not in found

    def test_search_by_content(self, tmp_path):
        """Test searching files by content."""
        tool = FileTool(project_dir=str(tmp_path))
        (tmp_path / "file1.txt").write_text("hello world python")
        (tmp_path / "file2.txt").write_text("hello java")
        (tmp_path / "file3.txt").write_text("something else")

        result = tool.search(content="python")
        assert result.success is True
        found = [item["name"] for item in result.data]
        assert "file1.txt" in found
        assert "file2.txt" not in found


class TestFileToolEdgeCases:
    """Test edge cases and error handling."""

    def test_path_with_parent_directory_traversal(self, tmp_path):
        """Test protection against .. traversal."""
        tool = FileTool(project_dir=str(tmp_path))
        # Create a file that might be targeted
        outside_file = tmp_path.parent / "outside.txt"
        outside_file.write_text("secret")

        # Try to read it using traversal
        result = tool.read("../outside.txt")
        assert result.success is False

    def test_symlink_to_outside_directory(self, tmp_path):
        """Test handling of symlinks pointing outside project."""
        tool = FileTool(project_dir=str(tmp_path))
        outside_dir = tmp_path.parent / "outside_dir"
        outside_dir.mkdir(exist_ok=True)
        (outside_dir / "secret.txt").write_text("secret")

        # Create symlink pointing outside
        symlink = tmp_path / "link_to_outside"
        try:
            symlink.symlink_to(outside_dir)
            # Try to read through symlink
            result = tool.read("link_to_outside/secret.txt")
            # Should be blocked as it's outside project
            assert result.success is False
        except (OSError, NotImplementedError):
            # Symlinks not supported on this platform
            pass
        finally:
            if symlink.exists():
                symlink.unlink()
            if outside_dir.exists():
                import shutil
                shutil.rmtree(outside_dir)

    def test_very_long_filename(self, tmp_path):
        """Test handling of very long filenames."""
        tool = FileTool(project_dir=str(tmp_path))
        long_name = "a" * 300 + ".txt"
        result = tool.write(long_name, "content")
        # Most filesystems have filename length limits
        assert result.success is False or (tmp_path / long_name).exists()

    def test_binary_content_in_text_mode(self, tmp_path):
        """Test handling of binary content."""
        tool = FileTool(project_dir=str(tmp_path))
        binary_data = bytes([0x00, 0x01, 0x02, 0xFF, 0xFE])
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(binary_data)

        result = tool.read("binary.bin")
        # Binary files should be rejected with an appropriate error
        assert result.success is False
        assert "binary" in result.message.lower()
