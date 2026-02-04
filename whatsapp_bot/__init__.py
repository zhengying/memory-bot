"""
WhatsApp Bot - WhatsApp integration for Memory Bot

This module provides WhatsApp bot functionality using whatsapp-web.js
or other WhatsApp integration methods.
"""

from whatsapp_bot.config import WhatsAppConfig, get_config
from whatsapp_bot.bot import WhatsAppBot

__all__ = [
    "WhatsAppConfig",
    "get_config",
    "WhatsAppBot",
]