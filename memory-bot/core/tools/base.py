"""
Base class and interfaces for tools.

All tools must inherit from the Tool ABC and implement the execute method.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ToolResult:
    """Result of a tool execution."""

    success: bool
    data: Any = None
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success_result(cls, data: Any = None, message: str = "", **metadata) -> "ToolResult":
        """Create a successful result."""
        return cls(success=True, data=data, message=message, metadata=metadata)

    @classmethod
    def failure_result(cls, message: str, data: Any = None, **metadata) -> "ToolResult":
        """Create a failed result."""
        return cls(success=False, data=data, message=message, metadata=metadata)


class ToolError(Exception):
    """Exception raised by tools."""

    def __init__(self, message: str, code: str = "TOOL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class Tool(ABC):
    """Abstract base class for all tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._enabled = True

    @property
    def enabled(self) -> bool:
        """Whether the tool is enabled."""
        return self._enabled

    def enable(self) -> None:
        """Enable the tool."""
        self._enabled = True

    def disable(self) -> None:
        """Disable the tool."""
        self._enabled = False

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with the given parameters.

        Args:
            **kwargs: Tool-specific parameters.

        Returns:
            ToolResult: The result of the execution.
        """
        pass

    def validate_params(self, required: list, provided: dict) -> None:
        """
        Validate that all required parameters are provided.

        Args:
            required: List of required parameter names.
            provided: Dictionary of provided parameters.

        Raises:
            ToolError: If a required parameter is missing.
        """
        missing = [param for param in required if param not in provided or provided[param] is None]
        if missing:
            raise ToolError(
                f"Missing required parameters: {', '.join(missing)}",
                code="MISSING_PARAMS"
            )
