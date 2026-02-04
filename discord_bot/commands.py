"""
Discord Bot Commands

Handles command parsing and execution for the Discord bot.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ParsedCommand:
    """Parsed command result"""
    type: str  # 'command', 'mention', 'none'
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    content: str = ""
    raw: str = ""


class CommandParser:
    """Parse Discord messages for commands and mentions
    
    Supports:
    - Prefix commands (e.g., !chat, !help)
    - Direct mentions (e.g., @Bot hello)
    """
    
    def __init__(self, prefix: str = "!", bot_id: Optional[str] = None):
        """Initialize parser
        
        Args:
            prefix: Command prefix character(s)
            bot_id: Bot's Discord user ID for mention detection
        """
        self.prefix = prefix
        self.bot_id = bot_id
        # Regex pattern for bot mention: <@BOT_ID> or <@!BOT_ID>
        self.mention_pattern = re.compile(
            rf'<@!?({bot_id})>' if bot_id else r'<@!?\d+>'
        )
    
    def parse(self, content: str) -> ParsedCommand:
        """Parse message content
        
        Args:
            content: Raw message content
            
        Returns:
            ParsedCommand with type and parsed data
        """
        if not content or not content.strip():
            return ParsedCommand(type="none", raw=content)
        
        content = content.strip()
        
        # Check for mention
        if self._is_mention(content):
            return self._parse_mention(content)
        
        # Check for command prefix
        if content.startswith(self.prefix):
            return self._parse_command(content)
        
        # Regular message
        return ParsedCommand(type="none", raw=content)
    
    def _is_mention(self, content: str) -> bool:
        """Check if message starts with bot mention"""
        if not self.bot_id:
            return False
        match = self.mention_pattern.match(content)
        return match is not None
    
    def _parse_mention(self, content: str) -> ParsedCommand:
        """Parse mention message"""
        # Remove mention from content
        clean_content = self.mention_pattern.sub('', content).strip()
        
        return ParsedCommand(
            type="mention",
            content=clean_content,
            raw=content
        )
    
    def _parse_command(self, content: str) -> ParsedCommand:
        """Parse command message"""
        # Remove prefix
        without_prefix = content[len(self.prefix):].strip()
        
        if not without_prefix:
            return ParsedCommand(type="none", raw=content)
        
        # Split into command and arguments
        parts = without_prefix.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        return ParsedCommand(
            type="command",
            command=command,
            args=args,
            content=without_prefix,
            raw=content
        )
    
    def update_bot_id(self, bot_id: str):
        """Update bot ID for mention detection"""
        self.bot_id = bot_id
        self.mention_pattern = re.compile(rf'<@!?({bot_id})>')


class CommandHandler:
    """Handle and execute Discord bot commands
    
    Integrates with the AgentEngine to process user requests.
    """
    
    def __init__(self, agent: Any):
        """Initialize command handler
        
        Args:
            agent: AgentEngine instance for processing requests
        """
        self.agent = agent
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
        
        # Command handlers mapping
        self.command_map = {
            "help": self._handle_help,
            "chat": self._handle_chat,
            "memory": self._handle_memory,
            "session": self._handle_session,
            "clear": self._handle_clear,
        }
    
    async def handle_command(
        self,
        command: str,
        args: List[str],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle a command
        
        Args:
            command: Command name
            args: Command arguments
            user_id: Discord user ID
            
        Returns:
            Response dict with success status and content
        """
        handler = self.command_map.get(command)
        
        if not handler:
            return {
                "success": False,
                "content": f"Unknown command: `{command}`. Type `!help` for available commands."
            }
        
        try:
            return await handler(args, user_id)
        except Exception as e:
            logger.error(f"Error handling command '{command}': {e}")
            return {
                "success": False,
                "content": f"An error occurred while processing the command: {str(e)}"
            }
    
    async def handle_mention(
        self,
        content: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Handle direct mention to bot
        
        Args:
            content: Message content (without mention)
            user_id: Discord user ID
            
        Returns:
            Response dict
        """
        return await self._handle_chat([content], user_id)
    
    async def _handle_help(self, args: List[str], user_id: str) -> Dict[str, Any]:
        """Handle !help command"""
        help_text = """
**🤖 Memory Bot - Available Commands**

**General Commands:**
`!help` - Show this help message
`!chat <message>` - Chat with the AI (also works with @mention)
`!clear` - Clear your current session history

**Session Commands:**
`!session info` - Show your current session info
`!session list` - List your recent sessions

**Memory Commands:**
`!memory search <query>` - Search your memory
`!memory stats` - Show memory statistics

**Tip:** You can also just @mention me to chat!
"""
        return {
            "success": True,
            "content": help_text
        }
    
    async def _handle_chat(self, args: List[str], user_id: str) -> Dict[str, Any]:
        """Handle !chat command or direct mention"""
        if not args:
            return {
                "success": False,
                "content": "Please provide a message. Usage: `!chat <message>`"
            }
        
        message = " ".join(args)
        
        # Get or create session for user
        session_id = self.user_sessions.get(user_id)
        
        # Call agent
        response = self.agent.chat(
            user_message=message,
            session_id=session_id,
            use_memory=True
        )
        
        # Store session for user
        self.user_sessions[user_id] = response["session_id"]
        
        return {
            "success": True,
            "content": response["content"],
            "metadata": {
                "session_id": response["session_id"],
                "tokens_used": response.get("tokens_used"),
                "memory_used": response.get("memory_used")
            }
        }
    
    async def _handle_memory(self, args: List[str], user_id: str) -> Dict[str, Any]:
        """Handle !memory command"""
        if not args:
            return {
                "success": False,
                "content": "Please specify a subcommand. Usage: `!memory <search|stats>`"
            }
        
        subcommand = args[0].lower()
        
        if subcommand == "search":
            if len(args) < 2:
                return {
                    "success": False,
                    "content": "Please provide a search query. Usage: `!memory search <query>`"
                }
            query = " ".join(args[1:])
            # TODO: Implement memory search
            return {
                "success": True,
                "content": f"🔍 Searching memory for: `{query}`\n\n(Memory search not yet implemented)"
            }
        
        elif subcommand == "stats":
            # TODO: Implement memory stats
            return {
                "success": True,
                "content": "📊 **Memory Statistics**\n\n(Memory stats not yet implemented)"
            }
        
        else:
            return {
                "success": False,
                "content": f"Unknown memory subcommand: `{subcommand}`. Use `search` or `stats`."
            }
    
    async def _handle_session(self, args: List[str], user_id: str) -> Dict[str, Any]:
        """Handle !session command"""
        if not args:
            return {
                "success": False,
                "content": "Please specify a subcommand. Usage: `!session <info|list>`"
            }
        
        subcommand = args[0].lower()
        session_id = self.user_sessions.get(user_id)
        
        if subcommand == "info":
            if not session_id:
                return {
                    "success": True,
                    "content": "📋 **Session Info**\n\nNo active session. Start chatting to create one!"
                }
            
            return {
                "success": True,
                "content": f"📋 **Session Info**\n\nSession ID: `{session_id}`\nUser ID: `{user_id}`"
            }
        
        elif subcommand == "list":
            # TODO: Implement session listing
            return {
                "success": True,
                "content": "📋 **Your Sessions**\n\n(Session listing not yet implemented)"
            }
        
        else:
            return {
                "success": False,
                "content": f"Unknown session subcommand: `{subcommand}`. Use `info` or `list`."
            }
    
    async def _handle_clear(self, args: List[str], user_id: str) -> Dict[str, Any]:
        """Handle !clear command - clear user's session"""
        if user_id in self.user_sessions:
            old_session = self.user_sessions[user_id]
            del self.user_sessions[user_id]
            
            return {
                "success": True,
                "content": f"🧹 **Session Cleared**\n\nPrevious session `{old_session}` has been cleared. Starting fresh!"
            }
        else:
            return {
                "success": True,
                "content": "🧹 **Session Cleared**\n\nNo active session to clear. You're already starting fresh!"
            }
