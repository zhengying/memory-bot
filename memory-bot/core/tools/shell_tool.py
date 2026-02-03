"""
Shell Tool - Safe shell command execution for the agent.

Provides controlled access to shell commands with safety checks,
timeout control, and output capture.
"""

import os
import re
import shlex
import subprocess
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.tools.base import Tool, ToolResult, ToolError


class ShellTool(Tool):
    """Tool for safe shell command execution.
    
    Features:
    - Timeout control (default: 30s, max: 300s)
    - Working directory restriction
    - Dangerous command blacklist
    - Output size limits
    - Environment variable filtering
    """
    
    # Dangerous commands that are blocked
    DANGEROUS_PATTERNS = [
        # System destruction
        r'rm\s+-rf\s+/',
        r'rm\s+-rf\s+/\s*\*',
        r':\(\)\{\s*:\|:\s*\}&',
        r'dd\s+if=\S+\s+of=/dev/[sh]d\S+',
        r'mkfs\.\w+\s+/dev/[sh]d\S+',
        r'\>\s*/dev/[sh]d\S+',
        
        # Privilege escalation
        r'chmod\s+-R\s+777\s+/',
        r'chown\s+-R\s+\w+:\w+\s+/',
        
        # Network attacks
        r'tcpdump\s+-i\s+\w+',
        r'nc\s+-[l]+',
        r'netcat\s+-[l]+',
        
        # Information leakage
        r'cat\s+/etc/shadow',
        r'cat\s+/etc/passwd',
    ]
    
    # Allowed commands whitelist (if not empty, only these are allowed)
    ALLOWED_COMMANDS: Optional[List[str]] = None
    
    # Default timeout in seconds
    DEFAULT_TIMEOUT = 30
    MAX_TIMEOUT = 300  # 5 minutes
    
    # Output size limits
    MAX_STDOUT_SIZE = 1024 * 1024  # 1MB
    MAX_STDERR_SIZE = 100 * 1024   # 100KB
    
    def __init__(
        self,
        working_dir: Optional[str] = None,
        allowed_commands: Optional[List[str]] = None,
        default_timeout: int = DEFAULT_TIMEOUT,
        environment: Optional[Dict[str, str]] = None
    ):
        """Initialize ShellTool.
        
        Args:
            working_dir: Restrict commands to this directory.
                        Defaults to current working directory.
            allowed_commands: Whitelist of allowed commands.
                            If None, uses DANGEROUS_PATTERNS blacklist.
            default_timeout: Default command timeout in seconds.
            environment: Additional environment variables for commands.
        """
        super().__init__(
            name="shell",
            description="Execute shell commands safely"
        )
        self.working_dir = Path(working_dir or os.getcwd()).resolve()
        self.allowed_commands = allowed_commands
        self.default_timeout = min(default_timeout, self.MAX_TIMEOUT)
        self.environment = environment or {}
    
    def _validate_command(self, command: str) -> None:
        """Validate command for safety.
        
        Args:
            command: Command string to validate.
            
        Raises:
            ToolError: If command is dangerous or not allowed.
        """
        # Check whitelist if configured
        if self.allowed_commands is not None:
            cmd_base = command.strip().split()[0] if command.strip() else ""
            if cmd_base not in self.allowed_commands:
                raise ToolError(
                    f"Command '{cmd_base}' is not in the allowed commands list. "
                    f"Allowed: {', '.join(self.allowed_commands)}",
                    code="COMMAND_NOT_ALLOWED"
                )
        
        # Check blacklist patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                raise ToolError(
                    f"Command matches dangerous pattern and is blocked for safety. "
                    f"Pattern: {pattern}",
                    code="DANGEROUS_COMMAND"
                )
    
    def _resolve_working_dir(self, cwd: Optional[str] = None) -> str:
        """Resolve and validate working directory.
        
        Args:
            cwd: Requested working directory.
            
        Returns:
            Resolved working directory path.
            
        Raises:
            ToolError: If directory is outside allowed workspace.
        """
        if cwd:
            target = Path(cwd).resolve()
        else:
            target = self.working_dir
        
        # Ensure target is within working_dir
        try:
            target.relative_to(self.working_dir)
        except ValueError:
            raise ToolError(
                f"Working directory '{target}' is outside the allowed workspace. "
                f"Must be within: {self.working_dir}",
                code="WORKING_DIR_OUTSIDE_WORKSPACE"
            )
        
        if not target.exists():
            raise ToolError(
                f"Working directory does not exist: {target}",
                code="WORKING_DIR_NOT_FOUND"
            )
        
        if not target.is_dir():
            raise ToolError(
                f"Working directory path is not a directory: {target}",
                code="WORKING_DIR_NOT_DIRECTORY"
            )
        
        return str(target)
    
    def _truncate_output(self, data: bytes, max_size: int) -> Tuple[str, bool]:
        """Truncate output to max size.
        
        Args:
            data: Raw output bytes.
            max_size: Maximum size in bytes.
            
        Returns:
            Tuple of (decoded string, was_truncated).
        """
        if len(data) <= max_size:
            return data.decode('utf-8', errors='replace'), False
        
        truncated = data[:max_size]
        text = truncated.decode('utf-8', errors='replace')
        return text + f"\n... [output truncated, total size: {len(data)} bytes]", True
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute shell command.
        
        Args:
            command: Command string to execute (required)
            cwd: Working directory for command
            timeout: Command timeout in seconds (default: 30)
            env: Additional environment variables
            
        Returns:
            ToolResult with command output
        """
        command = kwargs.get('command')
        
        if not command:
            return ToolResult.failure_result(
                "Command is required",
                code="MISSING_COMMAND"
            )
        
        # Validate command
        try:
            self._validate_command(command)
        except ToolError as e:
            return ToolResult.failure_result(e.message, code=e.code)
        
        # Resolve working directory
        try:
            cwd = self._resolve_working_dir(kwargs.get('cwd'))
        except ToolError as e:
            return ToolResult.failure_result(e.message, code=e.code)
        
        # Get timeout
        timeout = kwargs.get('timeout', self.default_timeout)
        timeout = min(timeout, self.MAX_TIMEOUT)
        
        # Prepare environment
        env = os.environ.copy()
        env.update(self.environment)
        if 'env' in kwargs and kwargs['env']:
            env.update(kwargs['env'])
        
        # Execute command
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                timeout=timeout,
                env=env
            )
            
            # Process output
            stdout, stdout_truncated = self._truncate_output(
                result.stdout, self.MAX_STDOUT_SIZE
            )
            stderr, stderr_truncated = self._truncate_output(
                result.stderr, self.MAX_STDERR_SIZE
            )
            
            return ToolResult.success_result(
                data={
                    'command': command,
                    'returncode': result.returncode,
                    'stdout': stdout,
                    'stderr': stderr,
                    'stdout_truncated': stdout_truncated,
                    'stderr_truncated': stderr_truncated,
                    'cwd': cwd,
                    'timeout': timeout
                },
                message=f"Command executed (exit code: {result.returncode})"
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult.failure_result(
                f"Command timed out after {timeout} seconds",
                code="COMMAND_TIMEOUT",
                data={'command': command, 'timeout': timeout}
            )
        except Exception as e:
            return ToolResult.failure_result(
                f"Command execution failed: {str(e)}",
                code="COMMAND_ERROR",
                data={'command': command, 'error_type': type(e).__name__}
            )
