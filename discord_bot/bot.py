"""
Discord Bot - Main Bot Class

This module provides the main Discord bot class that connects to Discord,
handles events, and integrates with the memory-bot AgentEngine.
"""

import logging
import asyncio
from typing import Optional, Any, Dict, List

import discord
from discord.ext import commands as discord_commands

from discord_bot.config import DiscordConfig, get_config
from discord_bot.commands import CommandParser, CommandHandler, ParsedCommand

# Configure logging
logger = logging.getLogger(__name__)


class DiscordBot:
    """Discord Bot with memory-bot integration
    
    This bot:
    1. Connects to Discord using discord.py
    2. Handles prefix commands (!help, !chat, etc.)
    3. Handles direct mentions (@Bot hello)
    4. Integrates with AgentEngine for AI responses
    5. Manages user sessions for context continuity
    
    Attributes:
        config: DiscordConfig instance
        agent: AgentEngine instance
        client: discord.Client instance
        parser: CommandParser for parsing messages
        command_handler: CommandHandler for executing commands
    """
    
    def __init__(
        self,
        config: Optional[DiscordConfig] = None,
        agent: Optional[Any] = None
    ):
        """Initialize Discord Bot
        
        Args:
            config: DiscordConfig instance (loads from env if None)
            agent: AgentEngine instance (must be provided)
        """
        self.config = config or get_config()
        self.agent = agent
        
        if not self.agent:
            raise ValueError("AgentEngine instance is required")
        
        # Initialize Discord intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required to read message content
        
        # Initialize Discord client
        self.client = discord.Client(
            intents=intents,
            description=self.config.description
        )
        
        # Initialize command parser and handler
        self.parser = CommandParser(
            prefix=self.config.command_prefix,
            bot_id=self.config.bot_id
        )
        self.command_handler = CommandHandler(agent=self.agent)
        
        # Register event handlers
        self._register_events()
        
        logger.info("DiscordBot initialized")
    
    def _register_events(self):
        """Register Discord event handlers"""
        
        @self.client.event
        async def on_ready():
            """Called when bot is ready"""
            logger.info(f"Bot logged in as {self.client.user}")
            
            # Update bot metadata in config
            self.config.bot_id = str(self.client.user.id)
            self.config.bot_name = self.client.user.name
            
            # Update parser with bot ID
            self.parser.update_bot_id(str(self.client.user.id))
            
            # Update presence
            await self.client.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.listening,
                    name=f"{self.config.command_prefix}help"
                )
            )
        
        @self.client.event
        async def on_message(message: discord.Message):
            """Called when a message is received"""
            await self.on_message(message)
        
        @self.client.event
        async def on_error(event: str, *args, **kwargs):
            """Called when an error occurs"""
            logger.error(f"Error in event {event}: {args}, {kwargs}")
    
    async def on_message(self, message: discord.Message):
        """Process incoming message
        
        Args:
            message: Discord message object
        """
        # Ignore messages from self
        if message.author.bot:
            return
        
        # Ignore messages from other bots (optional, but recommended)
        if message.author.bot and message.author.id != self.client.user.id:
            return
        
        try:
            # Parse the message
            parsed = self.parser.parse(message.content)
            
            if parsed.type == "command":
                await self._handle_command(message, parsed)
            elif parsed.type == "mention":
                await self._handle_mention(message, parsed)
            # else: regular message, ignore (or could be handled if needed)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await message.channel.send(
                "❌ An error occurred while processing your message. Please try again."
            )
    
    async def _handle_command(
        self,
        message: discord.Message,
        parsed: ParsedCommand
    ):
        """Handle a command message
        
        Args:
            message: Discord message object
            parsed: ParsedCommand object
        """
        logger.info(f"Processing command: {parsed.command} from user {message.author.id}")
        
        # Show typing indicator
        async with message.channel.typing():
            result = await self.command_handler.handle_command(
                command=parsed.command,
                args=parsed.args,
                user_id=str(message.author.id)
            )
        
        # Send response
        if result["success"]:
            await self._send_response(message.channel, result["content"])
        else:
            await self._send_response(
                message.channel,
                f"❌ {result['content']}",
                error=True
            )
    
    async def _handle_mention(
        self,
        message: discord.Message,
        parsed: ParsedCommand
    ):
        """Handle a direct mention
        
        Args:
            message: Discord message object
            parsed: ParsedCommand object
        """
        logger.info(f"Processing mention from user {message.author.id}")
        
        # Show typing indicator
        async with message.channel.typing():
            result = await self.command_handler.handle_mention(
                content=parsed.content,
                user_id=str(message.author.id)
            )
        
        # Send response
        if result["success"]:
            await self._send_response(message.channel, result["content"])
        else:
            await self._send_response(
                message.channel,
                f"❌ {result['content']}",
                error=True
            )
    
    async def _send_response(
        self,
        channel: discord.TextChannel,
        content: str,
        error: bool = False
    ):
        """Send response to channel, handling length limits
        
        Args:
            channel: Discord channel
            content: Message content
            error: Whether this is an error message
        """
        max_length = self.config.max_message_length
        
        if len(content) <= max_length:
            await channel.send(content)
        else:
            # Split into multiple messages
            chunks = self._split_message(content, max_length)
            for i, chunk in enumerate(chunks):
                if i == 0 and error:
                    chunk = f"❌ {chunk}"
                await channel.send(chunk)
    
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
    
    def start(self):
        """Start the Discord bot
        
        This method blocks until the bot is stopped.
        """
        logger.info("Starting Discord bot...")
        try:
            self.client.run(self.config.token)
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
    
    async def close(self):
        """Close the Discord bot connection"""
        logger.info("Closing Discord bot...")
        await self.client.close()
