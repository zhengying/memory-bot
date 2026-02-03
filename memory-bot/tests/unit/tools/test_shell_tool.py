"""Unit tests for ShellTool."""

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from core.tools.shell_tool import ShellTool


class TestShellToolInit:
    """Test ShellTool initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        tool = ShellTool()
        assert tool.name == "shell"
        assert "shell command" in tool.description.lower()
        assert tool.timeout == 30
        assert tool.allowed_dirs == []
        assert tool.blocked_commands == []

    def test_init_with_custom_values(self, tmp_path):
        """Test initialization with custom values."""
        allowed_dirs = [str(tmp_path), "/tmp"]
        blocked = ["rm", "dd"]
        tool = ShellTool(
            timeout=60,
            allowed_dirs=allowed_dirs,
            blocked_commands=blocked
        )
        assert tool.timeout == 60
        assert len(tool.allowed_dirs) == 2
        assert len(tool.blocked_commands) == 2

    def test_default_blocked_commands(self):
        """Test default blocked dangerous commands."""
        tool = ShellTool()
        defaults = tool._get_default_blocked_commands()
        assert "rm -rf /" in defaults
        assert "> /dev/sda" in defaults
        assert "mkfs" in defaults
        assert "dd if=/dev/zero" in defaults
        assert ":(){ :|:& };:" in defaults


class TestShellToolSecurity:
    """Test security features."""

    def test_is_command_blocked_exact_match(self):
        """Test blocking exact command matches."""
        tool = ShellTool(blocked_commands=["rm -rf /"])
        assert tool._is_command_blocked("rm -rf /") is True

    def test_is_command_blocked_partial_match(self):
        """Test blocking partial command matches."""
        tool = ShellTool()
        assert tool._is_command_blocked("rm -rf /home/user") is True
        assert tool._is_command_blocked("mkfs.ext4 /dev/sdb1") is True

    def test_is_command_blocked_not_blocked(self):
        """Test that safe commands are not blocked."""
        tool = ShellTool()
        assert tool._is_command_blocked("ls -la") is False
        assert tool._is_command_blocked("cat file.txt") is False
        assert tool._is_command_blocked("echo hello") is False

    def test_is_path_in_allowed_dirs_with_no_restrictions(self):
        """Test path check with no directory restrictions."""
        tool = ShellTool()
        assert tool._is_path_in_allowed_dirs("/any/path") is True

    def test_is_path_in_allowed_dirs_with_restrictions(self, tmp_path):
        """Test path check with directory restrictions."""
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        not_allowed = tmp_path / "not_allowed"
        not_allowed.mkdir()

        tool = ShellTool(allowed_dirs=[str(allowed)])
        assert tool._is_path_in_allowed_dirs(str(allowed / "file.txt")) is True
        assert tool._is_path_in_allowed_dirs(str(not_allowed / "file.txt")) is False


class TestShellToolExecute:
    """Test command execution."""

    def test_execute_simple_command(self):
        """Test executing a simple command."""
        tool = ShellTool()
        result = tool.execute("echo hello")
        assert result.success is True
        assert "hello" in result.data["stdout"]
        assert result.data["returncode"] == 0

    def test_execute_with_cwd(self, tmp_path):
        """Test executing command with working directory."""
        tool = ShellTool()
        result = tool.execute("pwd", cwd=str(tmp_path))
        assert result.success is True
        assert str(tmp_path) in result.data["stdout"]

    def test_execute_blocked_command(self):
        """Test that blocked commands are rejected."""
        tool = ShellTool()
        result = tool.execute("rm -rf /")
        assert result.success is False
        assert "blocked" in result.message.lower()

    def test_execute_with_timeout(self):
        """Test command timeout."""
        tool = ShellTool(timeout=1)
        result = tool.execute("sleep 10")
        assert result.success is False
        assert "timeout" in result.message.lower()

    def test_execute_with_env(self):
        """Test command with environment variables."""
        tool = ShellTool()
        result = tool.execute("echo $TEST_VAR", env={"TEST_VAR": "test_value"})
        assert result.success is True
        assert "test_value" in result.data["stdout"]


class TestShellToolParsers:
    """Test output parsing."""

    def test_parse_stdout_bytes(self):
        """Test parsing stdout bytes."""
        tool = ShellTool()
        result = tool._parse_output(b"hello\nworld", None)
        assert result["stdout"] == "hello\nworld"
        assert result["stderr"] == ""

    def test_parse_stderr_bytes(self):
        """Test parsing stderr bytes."""
        tool = ShellTool()
        result = tool._parse_output(None, b"error message")
        assert result["stdout"] == ""
        assert result["stderr"] == "error message"

    def test_parse_both_outputs(self):
        """Test parsing both stdout and stderr."""
        tool = ShellTool()
        result = tool._parse_output(b"output", b"error")
        assert result["stdout"] == "output"
        assert result["stderr"] == "error"


class TestShellToolErrorHandling:
    """Test error handling."""

    @patch("subprocess.run")
    def test_os_error_handling(self, mock_run):
        """Test handling of OS errors."""
        mock_run.side_effect = OSError("Command not found")
        tool = ShellTool()
        result = tool.execute("nonexistent_command")
        assert result.success is False
        assert "os error" in result.message.lower()

    @patch("subprocess.run")
    def test_subprocess_error_handling(self, mock_run):
        """Test handling of subprocess errors."""
        mock_run.side_effect = subprocess.SubprocessError("Subprocess failed")
        tool = ShellTool()
        result = tool.execute("some_command")
        assert result.success is False
        assert "subprocess error" in result.message.lower()

    def test_file_not_found_error(self):
        """Test handling of file not found during command execution."""
        tool = ShellTool()
        result = tool.execute("./nonexistent_script.sh")
        assert result.success is False
