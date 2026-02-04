"""
WhatsApp Bot - Main Bot Class

This module provides the main WhatsApp bot class that connects to WhatsApp,
handles messages, and integrates with the memory-bot AgentEngine.

Supports multiple WhatsApp integration methods:
- whatsapp-web.js (via Python bridge)
- pywhatkit (simple messaging)
- twilio (WhatsApp Business API)
"""

import logging
import asyncio
from typing import Optional, Any, Dict, List, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass

from whatsapp_bot.config import WhatsAppConfig, get_config
from whatsapp_bot.commands import CommandParser, CommandHandler, ParsedCommand

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class WhatsAppMessage:
    """Represents a WhatsApp message"""
    id: str
    from_number: str
    to_number: str
    content: str
    timestamp: Optional[str] = None
    is_group: bool = False
    sender_name: Optional[str] = None
    chat_id: Optional[str] = None


class WhatsAppAdapter(ABC):
    """Abstract base class for WhatsApp adapters
    
    This allows the bot to work with different WhatsApp
    integration methods (whatsapp-web.js, Twilio, etc.)
    """
    
    @abstractmethod
    async def connect(self):
        """Connect to WhatsApp"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from WhatsApp"""
        pass
    
    @abstractmethod
    async def send_message(self, to_number: str, content: str) -> bool:
        """Send a message
        
        Args:
            to_number: Recipient phone number
            content: Message content
            
        Returns:
            True if sent successfully
        """
        pass
    
    @abstractmethod
    def on_message(self, callback: Callable[[WhatsAppMessage], None]):
        """Register message handler
        
        Args:
            callback: Function to call when message is received
        """
        pass


class WhatsAppBot:
    """WhatsApp Bot with memory-bot integration
    
    This bot:
    1. Connects to WhatsApp using an adapter
    2. Handles commands (!help, !chat, etc.)
    3. Integrates with AgentEngine for AI responses
    4. Manages user sessions for context continuity
    
    Attributes:
        config: WhatsAppConfig instance
        agent: AgentEngine instance
        adapter: WhatsAppAdapter instance
        parser: CommandParser for parsing messages
        command_handler: CommandHandler for executing commands
    """
    
    def __init__(
        self,
        config: Optional[WhatsAppConfig] = None,
        agent: Optional[Any] = None,
        adapter: Optional[WhatsAppAdapter] = None
    ):
        """Initialize WhatsApp Bot
        
        Args:
            config: WhatsAppConfig instance (loads from env if None)
            agent: AgentEngine instance (must be provided)
            adapter: WhatsAppAdapter instance (creates default if None)
        """
        self.config = config or get_config()
        self.agent = agent
        
        if not self.agent:
            raise ValueError("AgentEngine instance is required")
        
        # Initialize WhatsApp adapter
        self.adapter = adapter or self._create_default_adapter()
        
        # Initialize command parser and handler
        self.parser = CommandParser(
            prefix=self.config.command_prefix,
            bot_number=self.config.phone_number
        )
        self.command_handler = CommandHandler(agent=self.agent)
        
        # Register message handler
        self.adapter.on_message(self._on_message)
        
        # State tracking
        self._running = False
        self._message_queue: asyncio.Queue = asyncio.Queue()
        
        logger.info("WhatsAppBot initialized")
    
    def _create_default_adapter(self) -> WhatsAppAdapter:
        """Create default WhatsApp adapter based on configuration
        
        Returns:
            WhatsAppAdapter instance
        """
        # For now, return a placeholder that should be replaced
        # In a real implementation, this would check config and create
        # the appropriate adapter (whatsapp-web.js bridge, Twilio, etc.)
        raise NotImplementedError(
            "WhatsApp adapter must be provided or configured. "
            "Please provide an adapter instance or configure the adapter type."
        )
    
    async def _on_message(self, message: WhatsAppMessage):
        """Handle incoming WhatsApp message
        
        Args:
            message: WhatsAppMessage object
        """
        # Put message in queue for processing
        await self._message_queue.put(message)
    
    async def _process_messages(self):
        """Process messages from the queue"""
        while self._running:
            try:
                # Get message with timeout to allow checking _running
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=1.0
                )
                await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    async def _handle_message(self, message: WhatsAppMessage):
        """Process a single message
        
        Args:
            message: WhatsAppMessage object
        """
        # Skip group messages (optional, can be configurable)
        if message.is_group and not self.config.auto_reply:
            return
        
        # Skip empty messages
        if not message.content or not message.content.strip():
            return
        
        # Parse the message
        parsed = self.parser.parse(message.content)
        
        try:
            if parsed.type == "command":
                await self._handle_command(message, parsed)
            elif parsed.type == "mention":
                await self._handle_mention(message, parsed)
            elif parsed.type == "auto_reply" and self.config.auto_reply:
                # Treat as direct message for auto-reply mode
                await self._handle_direct_message(message, parsed.content)
            # else: ignore regular messages in non-auto-reply mode
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self._send_message(
                message.from_number,
                "❌ An error occurred while processing your message. Please try again."
            )
    
    async def _handle_command(
        self,
        message: WhatsAppMessage,
        parsed: ParsedCommand
    ):
        """Handle a command message
        
        Args:
            message: WhatsAppMessage object
            parsed: ParsedCommand object
        """
        logger.info(f"Processing command: {parsed.command} from user {message.from_number}")
        
        result = await self.command_handler.handle_command(
            command=parsed.command,
            args=parsed.args,
            user_id=message.from_number
        )
        
        # Send response
        if result["success"]:
            await self._send_message(message.from_number, result["content"])
        else:
            await self._send_message(
                message.from_number,
                f"❌ {result['content']}"
            )
    
    async def _handle_mention(
        self,
        message: WhatsAppMessage,
        parsed: ParsedCommand
    ):
        """Handle a direct mention
        
        Args:
            message: WhatsAppMessage object
            parsed: ParsedCommand object
        """
        logger.info(f"Processing mention from user {message.from_number}")
        
        result = await self.command_handler.handle_mention(
            content=parsed.content,
            user_id=message.from_number
        )
        
        # Send response
        if result["success"]:
            await self._send_message(message.from_number, result["content"])
        else:
            await self._send_message(
                message.from_number,
                f"❌ {result['content']}"
            )
    
    async def _handle_direct_message(
        self,
        message: WhatsAppMessage,
        content: str
    ):
        """Handle direct message (auto-reply mode)
        
        Args:
            message: WhatsAppMessage object
            content: Message content
        """
        logger.info(f"Processing direct message from user {message.from_number}")
        
        result = await self.command_handler.handle_mention(
            content=content,
            user_id=message.from_number
        )
        
        # Send response
        if result["success"]:
            await self._send_message(message.from_number, result["content"])
        else:
            await self._send_message(
                message.from_number,
                f"❌ {result['content']}"
            )
    
    async def _send_message(self, to_number: str, content: str):
        """Send a WhatsApp message
        
        Args:
            to_number: Recipient phone number
            content: Message content
        """
        # Split long messages
        max_length = self.config.max_message_length
        
        if len(content) <= max_length:
            await self.adapter.send_message(to_number, content)
        else:
            # Split into multiple messages
            chunks = self._split_message(content, max_length)
            for chunk in chunks:
                await self.adapter.send_message(to_number, chunk)
    
    def _split_message(self, content: str, max_length: int) -> List[str]:
        """Split long message into chunks
        
        Args:
            content: Message content
            max_length: Maximum chunk length
            
        Returns:
            List of message chunks
        """
        chunks = []
        current_chunk = ""
        
        # Try to split at newlines first
        lines = content.split('\n')
        
        for line in lines:
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk += line + '\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.rstrip())
                current_chunk = line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.rstrip())
        
        # If any chunk is still too long, force split
        final_chunks = []
        for chunk in chunks:
            while len(chunk) > max_length:
                final_chunks.append(chunk[:max_length])
                chunk = chunk[max_length:]
            if chunk:
                final_chunks.append(chunk)
        
        return final_chunks if final_chunks else [content[:max_length]]
    
    async def start(self):
        """Start the WhatsApp bot"""
        logger.info("Starting WhatsApp bot...")
        
        # Validate config
        errors = self.config.validate()
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        # Connect to WhatsApp
        await self.adapter.connect()
        
        # Start processing messages
        self._running = True
        await self._process_messages()
    
    async def stop(self):
        """Stop the WhatsApp bot"""
        logger.info("Stopping WhatsApp bot...")
        self._running = False
        await self.adapter.disconnect()