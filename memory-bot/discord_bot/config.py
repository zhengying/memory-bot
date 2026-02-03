"""
Discord Bot Configuration

Handles environment variables and configuration for the Discord bot.
"""

import os
from typing import Optional, List


class DiscordConfig:
    """Configuration for Discord Bot
    
    Loads configuration from environment variables.
    
    Required:
        DISCORD_TOKEN: Discord bot token
    
    Optional:
        DISCORD_COMMAND_PREFIX: Command prefix (default: !)
        DISCORD_OWNER_IDS: Comma-separated list of owner user IDs
        DISCORD_MAX_MESSAGE_LENGTH: Max message length (default: 2000)
        DISCORD_DEFAULT_SESSION_TIMEOUT: Session timeout in minutes (default: 60)
        DISCORD_LOG_LEVEL: Logging level (default: INFO)
    """
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        # Required
        self.token = self._get_required_env("DISCORD_TOKEN")
        
        # Optional with defaults
        self.command_prefix = self._get_env("DISCORD_COMMAND_PREFIX", "!")
        self.description = self._get_env(
            "DISCORD_DESCRIPTION",
            "Memory Bot - AI with long-term memory"
        )
        self.owner_ids = self._parse_id_list(
            self._get_env("DISCORD_OWNER_IDS", "")
        )
        self.max_message_length = int(
            self._get_env("DISCORD_MAX_MESSAGE_LENGTH", "2000")
        )
        self.default_session_timeout = int(
            self._get_env("DISCORD_DEFAULT_SESSION_TIMEOUT", "60")
        )
        self.log_level = self._get_env("DISCORD_LOG_LEVEL", "INFO")
        
        # Bot metadata (will be set after bot starts)
        self.bot_id: Optional[str] = None
        self.bot_name: Optional[str] = None
    
    def _get_env(self, key: str, default: str) -> str:
        """Get environment variable with default"""
        return os.environ.get(key, default)
    
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable
        
        Raises:
            ValueError: If environment variable is not set
        """
        value = os.environ.get(key)
        if not value:
            raise ValueError(
                f"Required environment variable {key} is not set. "
                f"Please set it before running the bot."
            )
        return value
    
    def _parse_id_list(self, value: str) -> List[str]:
        """Parse comma-separated list of IDs"""
        if not value:
            return []
        return [id.strip() for id in value.split(",") if id.strip()]
    
    def is_owner(self, user_id: str) -> bool:
        """Check if user is a bot owner
        
        Args:
            user_id: Discord user ID
            
        Returns:
            True if user is an owner
        """
        return user_id in self.owner_ids
    
    def validate(self) -> List[str]:
        """Validate configuration
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not self.token:
            errors.append("DISCORD_TOKEN is required")
        
        if len(self.command_prefix) > 5:
            errors.append("Command prefix too long (max 5 characters)")
        
        if self.max_message_length < 100:
            errors.append("Max message length too small (min 100)")
        
        return errors


# Global config instance
_config: Optional[DiscordConfig] = None


def get_config() -> DiscordConfig:
    """Get or create global config instance
    
    Returns:
        DiscordConfig instance
    """
    global _config
    if _config is None:
        _config = DiscordConfig()
    return _config


def reset_config():
    """Reset global config instance
    
    Useful for testing.
    """
    global _config
    _config = None
