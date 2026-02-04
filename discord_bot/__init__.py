"""
Discord Bot Module for Memory Bot

This module provides Discord integration for the memory-driven AI bot,
allowing users to interact with the AI through Discord messages and commands.

Example:
    from discord_bot import DiscordBot, DiscordConfig
    from core.agent import AgentEngine
    from core.llm import MockLLMProvider
    
    # Setup
    llm = MockLLMProvider(api_key="test", model="gpt-4")
    agent = AgentEngine(llm_provider=llm)
    config = DiscordConfig()
    
    # Start bot
    bot = DiscordBot(config=config, agent=agent)
    bot.start()
"""

__version__ = "0.1.0"
__author__ = "memory-bot"

# Imports for convenience
from discord_bot.config import DiscordConfig, get_config, reset_config
from discord_bot.commands import CommandParser, CommandHandler, ParsedCommand
from discord_bot.bot import DiscordBot

__all__ = [
    # Config
    "DiscordConfig",
    "get_config",
    "reset_config",
    
    # Commands
    "CommandParser",
    "CommandHandler", 
    "ParsedCommand",
    
    # Bot
    "DiscordBot",
    
    # Metadata
    "__version__",
    "__author__",
]
