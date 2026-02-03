"""
Tools Module - Infrastructure for Agent capabilities.

This module provides core tools that extend the agent's capabilities:
- FileTool: Safe file operations
- SearchTool: Web search capabilities
- ShellTool: Safe shell command execution

Example:
    from core.tools import FileTool, SearchTool, ShellTool
    
    # File operations
    file_tool = FileTool()
    result = file_tool.execute(operation='read', path='data.txt')
    
    # Web search
    search_tool = SearchTool()
    result = search_tool.execute(operation='text', query='Python tutorials')
    
    # Shell commands
    shell_tool = ShellTool()
    result = shell_tool.execute(command='ls -la')
"""

__version__ = "0.1.0"

# Base classes
from core.tools.base import (
    Tool,
    ToolResult,
    ToolError
)

# Tool implementations
from core.tools.file_tool import FileTool
from core.tools.search_tool import SearchTool
from core.tools.shell_tool import ShellTool

# Export all public classes
__all__ = [
    # Base
    "Tool",
    "ToolResult", 
    "ToolError",
    
    # Tools
    "FileTool",
    "SearchTool",
    "ShellTool",
    
    # Metadata
    "__version__"
]
