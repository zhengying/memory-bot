"""
WhatsApp Adapters

Provides different adapters for WhatsApp integration:
- TwilioAdapter: Official WhatsApp Business API via Twilio
- WebAdapter: WhatsApp Web automation (for development)
"""

from whatsapp_bot.adapters.base import WhatsAppAdapter, WhatsAppMessage

__all__ = [
    "WhatsAppAdapter",
    "WhatsAppMessage",
]