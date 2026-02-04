"""
WhatsApp Bot Configuration

Handles environment variables and configuration for the WhatsApp bot.
"""

import os
from typing import Optional, List


class WhatsAppConfig:
    """Configuration for WhatsApp Bot
    
    Loads configuration from environment variables.
    
    Required (choose one method):
        WHATSAPP_PHONE_NUMBER: Your WhatsApp phone number (for QR code method)
        WHATSAPP_SESSION_ID: Existing session ID to restore
        
    Optional:
        WHATSAPP_COMMAND_PREFIX: Command prefix (default: !)
        WHATSAPP_OWNER_NUMBERS: Comma-separated list of owner phone numbers
        WHATSAPP_MAX_MESSAGE_LENGTH: Max message length (default: 4000)
        WHATSAPP_DEFAULT_SESSION_TIMEOUT: Session timeout in minutes (default: 60)
        WHATSAPP_LOG_LEVEL: Logging level (default: INFO)
        WHATSAPP_QR_TIMEOUT: QR code scan timeout in seconds (default: 60)
        WHATSAPP_AUTO_REPLY: Enable auto-reply to all messages (default: False)
    """
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        # WhatsApp connection settings
        self.phone_number = self._get_env("WHATSAPP_PHONE_NUMBER", "")
        self.session_id = self._get_env("WHATSAPP_SESSION_ID", "memory-bot-session")
        
        # Command and message settings
        self.command_prefix = self._get_env("WHATSAPP_COMMAND_PREFIX", "!")
        self.description = self._get_env(
            "WHATSAPP_DESCRIPTION",
            "Memory Bot - AI with long-term memory"
        )
        self.owner_numbers = self._parse_number_list(
            self._get_env("WHATSAPP_OWNER_NUMBERS", "")
        )
        self.max_message_length = int(
            self._get_env("WHATSAPP_MAX_MESSAGE_LENGTH", "4000")
        )
        self.default_session_timeout = int(
            self._get_env("WHATSAPP_DEFAULT_SESSION_TIMEOUT", "60")
        )
        self.log_level = self._get_env("WHATSAPP_LOG_LEVEL", "INFO")
        
        # WhatsApp-specific settings
        self.qr_timeout = int(self._get_env("WHATSAPP_QR_TIMEOUT", "60"))
        self.auto_reply = self._get_env("WHATSAPP_AUTO_REPLY", "false").lower() == "true"
        
        # Bot metadata (will be set after bot starts)
        self.bot_id: Optional[str] = None
        self.bot_name: Optional[str] = None
    
    def _get_env(self, key: str, default: str) -> str:
        """Get environment variable with default"""
        return os.environ.get(key, default)
    
    def _parse_number_list(self, value: str) -> List[str]:
        """Parse comma-separated list of phone numbers"""
        if not value:
            return []
        # Normalize phone numbers (remove spaces, ensure + prefix)
        numbers = []
        for num in value.split(","):
            num = num.strip().replace(" ", "")
            if num:
                if not num.startswith("+"):
                    num = "+" + num
                numbers.append(num)
        return numbers
    
    def is_owner(self, phone_number: str) -> bool:
        """Check if user is a bot owner
        
        Args:
            phone_number: Phone number with country code
            
        Returns:
            True if user is an owner
        """
        # Normalize phone number
        normalized = phone_number.strip().replace(" ", "")
        if not normalized.startswith("+"):
            normalized = "+" + normalized
        
        return normalized in self.owner_numbers
    
    def validate(self) -> List[str]:
        """Validate configuration
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not self.phone_number and not self.session_id:
            errors.append("Either WHATSAPP_PHONE_NUMBER or WHATSAPP_SESSION_ID is required")
        
        if len(self.command_prefix) > 5:
            errors.append("Command prefix too long (max 5 characters)")
        
        if self.max_message_length < 100:
            errors.append("Max message length too small (min 100)")
        
        if self.qr_timeout < 10:
            errors.append("QR timeout too small (min 10 seconds)")
        
        return errors


# Global config instance
_config: Optional[WhatsAppConfig] = None


def get_config() -> WhatsAppConfig:
    """Get or create global config instance
    
    Returns:
        WhatsAppConfig instance
    """
    global _config
    if _config is None:
        _config = WhatsAppConfig()
    return _config


def reset_config():
    """Reset global config instance
    
    Useful for testing.
    """
    global _config
    _config = None