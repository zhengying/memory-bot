"""
File tool for reading, writing, and managing files.

Provides secure file operations with path validation to prevent directory traversal attacks.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .base import Tool, ToolError, ToolResult


class FileTool(Tool):
    """
    Tool for file operations with security checks.

    All file paths are validated to ensure they stay within the project directory.
    """

    def __init__(self, project_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the file tool.

        Args:
            project_dir: Base directory for all file operations.
                        Defaults to the current working directory.
        """
        super().__init__(
            name="file",
            description="Read, write, list, and search files within the project directory"
        )
        if project_dir is None:
            project_dir = Path.cwd()
        self.project_dir = Path(project_dir).resolve()

    def _resolve_path(self, path: Union[str, Path]) -> Path:
        """
        Resolve a path relative to the project directory.

        Args:
            path: The path to resolve.

        Returns:
            Path: The absolute, resolved path.
        """
        if isinstance(path, str):
            path = Path(path)

        if path.is_absolute():
            return path.resolve()
        else:
            return (self.project_dir / path).resolve()

    def _is_path_safe(self, path: Union[str, Path]) -> bool:
        """
        Check if a path is within the project directory.

        Args:
            path: The path to check.

        Returns:
            bool: True if the path is safe, False otherwise.
        """
        try:
            resolved = self._resolve_path(path)
            # Check if the resolved path is within or equal to project_dir
            return str(resolved).startswith(str(self.project_dir))
        except (ValueError, RuntimeError):
            return False

    def read(self, path: Union[str, Path]) -> ToolResult:
        """
        Read the contents of a file.

        Args:
            path: Path to the file (relative to project_dir or absolute).

        Returns:
            ToolResult: The file contents or error message.
        """
        try:
            if not self._is_path_safe(path):
                return ToolResult.failure_result(
                    f"Access denied: Path '{path}' is outside the allowed directory"
                )

            resolved_path = self._resolve_path(path)

            if not resolved_path.exists():
                return ToolResult.failure_result(
                    f"File not found: '{path}' does not exist"
                )

            if not resolved_path.is_file():
                return ToolResult.failure_result(
                    f"Not a file: '{path}' is a directory"
                )

            content = resolved_path.read_text(encoding="utf-8")

            # Try to parse as JSON if it looks like JSON
            if resolved_path.suffix in (".json",) or content.strip().startswith(("{", "[")):
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    pass  # Return as text if JSON parsing fails

            return ToolResult.success_result(
                data=content,
                message=f"Successfully read file: {path}"
            )

        except UnicodeDecodeError:
            return ToolResult.failure_result(
                f"Cannot read '{path}' as text: appears to be a binary file"
            )
        except Exception as e:
            return ToolResult.failure_result(
                f"Error reading file '{path}': {str(e)}"
            )

    def write(
        self,
        path: Union[str, Path],
        content: Union[str, dict, list],
        mode: str = "overwrite"
    ) -> ToolResult:
        """
        Write content to a file.

        Args:
            path: Path to the file (relative to project_dir or absolute).
            content: Content to write (string or JSON-serializable object).
            mode: Write mode - "overwrite" (default) or "append".

        Returns:
            ToolResult: Success or error message.
        """
        try:
            if not self._is_path_safe(path):
                return ToolResult.failure_result(
                    f"Access denied: Path '{path}' is outside the allowed directory"
                )

            if mode not in ("overwrite", "append"):
                return ToolResult.failure_result(
                    f"Invalid mode: '{mode}'. Use 'overwrite' or 'append'"
                )

            resolved_path = self._resolve_path(path)

            # Ensure parent directory exists
            resolved_path.parent.mkdir(parents=True, exist_ok=True)

            # Serialize content if needed
            if isinstance(content, (dict, list)):
                content = json.dumps(content, indent=2, ensure_ascii=False)

            # Write file
            write_mode = "a" if mode == "append" else "w"
            with open(resolved_path, write_mode, encoding="utf-8") as f:
                f.write(content)

            action = "appended to" if mode == "append" else "wrote"
            return ToolResult.success_result(
                message=f"Successfully {action} file: {path}"
            )

        except Exception as e:
            return ToolResult.failure_result(
                f"Error writing file '{path}': {str(e)}"
            )

    def list(
        self,
        path: Union[str, Path] = ".",
        recursive: bool = False
    ) -> ToolResult:
        """
        List files and directories.

        Args:
            path: Directory path (relative to project_dir or absolute).
            recursive: Whether to list recursively.

        Returns:
            ToolResult: List of files and directories.
        """
        try:
            if not self._is_path_safe(path):
                return ToolResult.failure_result(
                    f"Access denied: Path '{path}' is outside the allowed directory"
                )

            resolved_path = self._resolve_path(path)

            if not resolved_path.exists():
                return ToolResult.failure_result(
                    f"Directory not found: '{path}' does not exist"
                )

            if not resolved_path.is_dir():
                return ToolResult.failure_result(
                    f"Not a directory: '{path}' is a file"
                )

            def list_directory(dir_path: Path, is_recursive: bool) -> list:
                items = []
                try:
                    for item in sorted(dir_path.iterdir()):
                        item_info = {
                            "name": item.name,
                            "path": str(item.relative_to(self.project_dir)),
                            "type": "directory" if item.is_dir() else "file",
                            "size": item.stat().st_size if item.is_file() else None,
                        }

                        if item.is_dir() and is_recursive:
                            item_info["children"] = list_directory(item, True)

                        items.append(item_info)
                except PermissionError:
                    pass  # Skip directories we can't access
                return items

            items = list_directory(resolved_path, recursive)

            return ToolResult.success_result(
                data=items,
                message=f"Listed {len(items)} items in '{path}'"
            )

        except Exception as e:
            return ToolResult.failure_result(
                f"Error listing directory '{path}': {str(e)}"
            )

    def search(
        self,
        pattern: str = "",
        content: str = "",
        path: Union[str, Path] = "."
    ) -> ToolResult:
        """
        Search for files by name pattern or content.

        Args:
            pattern: Glob pattern for file names (e.g., "*.py").
            content: Text to search for in file contents.
            path: Directory to search in.

        Returns:
            ToolResult: List of matching files.
        """
        try:
            if not self._is_path_safe(path):
                return ToolResult.failure_result(
                    f"Access denied: Path '{path}' is outside the allowed directory"
                )

            if not pattern and not content:
                return ToolResult.failure_result(
                    "Either 'pattern' or 'content' must be specified"
                )

            resolved_path = self._resolve_path(path)
            matches = []

            if pattern:
                # Search by filename pattern
                for file_path in resolved_path.rglob(pattern):
                    if file_path.is_file():
                        matches.append({
                            "name": file_path.name,
                            "path": str(file_path.relative_to(self.project_dir)),
                            "type": "file",
                            "match_type": "filename"
                        })

            if content:
                # Search by file content
                for file_path in resolved_path.rglob("*"):
                    if file_path.is_file():
                        try:
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                file_content = f.read()
                                if content in file_content:
                                    matches.append({
                                        "name": file_path.name,
                                        "path": str(file_path.relative_to(self.project_dir)),
                                        "type": "file",
                                        "match_type": "content"
                                    })
                        except Exception:
                            continue

            # Remove duplicates
            seen = set()
            unique_matches = []
            for match in matches:
                key = match["path"]
                if key not in seen:
                    seen.add(key)
                    unique_matches.append(match)

            return ToolResult.success_result(
                data=unique_matches,
                message=f"Found {len(unique_matches)} matches"
            )

        except Exception as e:
            return ToolResult.failure_result(
                f"Error searching files: {str(e)}"
            )

    def execute(self, **kwargs) -> ToolResult:
        """
        Execute a file operation based on the action parameter.

        Args:
            action: The operation to perform (read, write, list, search).
            **kwargs: Additional parameters for the specific action.

        Returns:
            ToolResult: The result of the operation.
        """
        action = kwargs.get("action", "read")

        if action == "read":
            return self.read(kwargs.get("path", ""))
        elif action == "write":
            return self.write(
                path=kwargs.get("path", ""),
                content=kwargs.get("content", ""),
                mode=kwargs.get("mode", "overwrite")
            )
        elif action == "list":
            return self.list(
                path=kwargs.get("path", "."),
                recursive=kwargs.get("recursive", False)
            )
        elif action == "search":
            return self.search(
                pattern=kwargs.get("pattern", ""),
                content=kwargs.get("content", ""),
                path=kwargs.get("path", ".")
            )
        else:
            return ToolResult.failure_result(f"Unknown action: {action}")
