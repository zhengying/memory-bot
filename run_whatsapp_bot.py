#!/usr/bin/env python3
"""
WhatsApp Bot Runner - Simple Test Script

This script demonstrates how to run the WhatsApp Bot for testing.
It uses MockLLMProvider so you can test without an OpenAI API key.

Usage:
    python run_whatsapp_bot.py

Requirements:
    - Set environment variables (see README_WHATSAPP.md)
    - Install dependencies: pip install -e ".[whatsapp]"
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check required environment variables"""
    required_vars = []
    
    # Check provider-specific requirements
    provider = os.getenv("WHATSAPP_PROVIDER", "twilio").lower()
    
    if provider == "twilio":
        required_vars = [
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN", 
            "TWILIO_PHONE_NUMBER"
        ]
    elif provider == "whatsapp-business":
        required_vars = [
            "WHATSAPP_ACCESS_TOKEN",
            "WHATSAPP_PHONE_NUMBER_ID"
        ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.error("Missing required environment variables:")
        for var in missing:
            logger.error(f"  - {var}")
        logger.error("\nPlease set these variables before running the bot.")
        logger.error("See README_WHATSAPP.md for more information.")
        return False
    
    return True


def create_mock_agent():
    """Create a mock agent for testing without OpenAI API"""
    try:
        from core.llm.mock import MockLLMProvider
        from core.agent import AgentEngine
        
        logger.info("Creating Mock LLM Provider for testing...")
        
        # Create mock provider with predefined responses
        llm = MockLLMProvider(api_key="test", model="gpt-4")
        
        # Create agent engine
        agent = AgentEngine(llm_provider=llm)
        
        logger.info("Mock agent created successfully!")
        return agent
        
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.error("Make sure you're running from the project root directory.")
        sys.exit(1)


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("WhatsApp Bot Test Runner")
    logger.info("=" * 60)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Create agent (mock for testing)
    agent = create_mock_agent()
    
    # Import and create WhatsApp bot
    try:
        from whatsapp_bot import WhatsAppBot, WhatsAppConfig
        
        logger.info("Creating WhatsApp Bot...")
        config = WhatsAppConfig()
        bot = WhatsAppBot(config=config, agent=agent)
        
        # Start bot
        host = os.getenv("WHATSAPP_HOST", "0.0.0.0")
        port = int(os.getenv("WHATSAPP_PORT", "5000"))
        
        logger.info("-" * 60)
        logger.info(f"WhatsApp Bot is starting...")
        logger.info(f"Listening on {host}:{port}")
        logger.info(f"Webhook URL: http://{host}:{port}/webhook")
        logger.info("-" * 60)
        logger.info("To test locally, use ngrok to expose the webhook:")
        logger.info("  ngrok http 5000")
        logger.info("Then configure the webhook URL in your provider dashboard.")
        logger.info("-" * 60)
        
        bot.start(host=host, port=port)
        
    except Exception as e:
        logger.error(f"Failed to start WhatsApp Bot: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
