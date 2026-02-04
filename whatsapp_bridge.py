#!/usr/bin/env python3
"""
Memory-Bot WhatsApp Bridge

This module provides OpenClaw-style channel integration for WhatsApp.
Instead of implementing a full WhatsApp Bot, it uses webhooks to receive
messages and forwards them to the memory-bot Agent.

Usage:
    1. Configure environment variables
    2. Run: python whatsapp_bridge.py
    3. Set webhook URL in your WhatsApp provider (Twilio, etc.)

Environment Variables:
    - WHATSAPP_PROVIDER: "twilio" or "whatsapp-business"
    - TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
    - WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID
    - OPENAI_API_KEY: For the AI responses
    - WEBHOOK_SECRET: For validating webhooks
    - PORT: Server port (default: 5000)
"""

import os
import sys
import json
import hmac
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


class WhatsAppBridge:
    """
    WhatsApp Bridge for Memory-Bot
    
    This class provides a simple webhook-based integration for WhatsApp.
    It receives messages via webhooks, processes them using the memory-bot
    Agent, and sends responses back.
    
    Similar to OpenClaw's channel approach, this bridge handles:
    - Webhook reception and validation
    - Message parsing and formatting
    - Agent interaction
    - Response sending
    """
    
    def __init__(self):
        self.app = Flask(__name__)
        self._setup_routes()
        self._init_agent()
        
        # Configuration
        self.provider = os.getenv("WHATSAPP_PROVIDER", "twilio")
        self.webhook_secret = os.getenv("WEBHOOK_SECRET", "")
        
        # Session tracking
        self.user_sessions: Dict[str, str] = {}
        
        logger.info(f"WhatsApp Bridge initialized with provider: {self.provider}")
    
    def _init_agent(self):
        """Initialize the memory-bot Agent"""
        try:
            from core.llm.openai import OpenAIProvider
            from core.agent import AgentEngine
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY not set. Using mock provider for testing.")
                from core.llm.mock import MockLLMProvider
                llm = MockLLMProvider(api_key="test", model="gpt-4")
            else:
                llm = OpenAIProvider(api_key=api_key, model="gpt-4")
            
            self.agent = AgentEngine(llm_provider=llm)
            logger.info("Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/webhook', methods=['GET', 'POST'])
        def webhook():
            """Handle incoming webhook"""
            if request.method == 'GET':
                return self._handle_verification()
            else:
                return self._handle_message()
        
        @self.app.route('/status', methods=['GET'])
        def status():
            """Health check"""
            return jsonify({
                "status": "ok",
                "provider": self.provider,
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.route('/', methods=['GET'])
        def index():
            """Root endpoint"""
            return jsonify({
                "service": "Memory-Bot WhatsApp Bridge",
                "version": "1.0.0",
                "provider": self.provider,
                "docs": "/status"
            })
    
    def _handle_verification(self):
        """Handle webhook verification"""
        challenge = request.args.get('hub.challenge')
        verify_token = request.args.get('hub.verify_token')
        
        if self.webhook_secret and verify_token == self.webhook_secret:
            return challenge, 200
        
        return "OK", 200
    
    def _handle_message(self):
        """Handle incoming message"""
        try:
            data = request.get_json() or request.form.to_dict()
            
            # Parse based on provider
            if self.provider == "twilio":
                message_data = self._parse_twilio(data)
            else:
                message_data = self._parse_whatsapp_business(data)
            
            if not message_data:
                return jsonify({"status": "ok"}), 200
            
            # Process message
            self._process_message(message_data)
            
            return jsonify({"status": "ok"}), 200
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _parse_twilio(self, data: Dict) -> Optional[Dict]:
        """Parse Twilio webhook data"""
        from_number = data.get('From', '').replace('whatsapp:', '')
        body = data.get('Body', '').strip()
        
        if not from_number or not body:
            return None
        
        return {
            "from": from_number,
            "body": body,
            "to": data.get('To', '').replace('whatsapp:', '')
        }
    
    def _parse_whatsapp_business(self, data: Dict) -> Optional[Dict]:
        """Parse WhatsApp Business API data"""
        try:
            entry = data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            
            if 'messages' not in value:
                return None
            
            messages = value.get('messages', [])
            if not messages:
                return None
            
            message = messages[0]
            contacts = value.get('contacts', [{}])[0]
            
            if message.get('type') != 'text':
                return None
            
            return {
                "from": contacts.get('wa_id', ''),
                "body": message.get('text', {}).get('body', ''),
                "to": value.get('metadata', {}).get('phone_number_id', '')
            }
            
        except Exception as e:
            logger.error(f"Error parsing WhatsApp Business message: {e}")
            return None
    
    def _process_message(self, message_data: Dict):
        """Process message and send response"""
        from_number = message_data["from"]
        body = message_data["body"]
        
        logger.info(f"Processing message from {from_number}: {body[:50]}...")
        
        try:
            # Simple command parsing
            if body.startswith('!'):
                response = self._handle_command(body, from_number)
            else:
                # Treat as chat message
                response = self._handle_chat(body, from_number)
            
            # Send response
            self._send_response(from_number, response)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self._send_response(from_number, "Sorry, an error occurred. Please try again.")
    
    def _handle_command(self, command: str, user_id: str) -> str:
        """Handle command"""
        parts = command[1:].split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd == "help":
            return """
🤖 *Memory Bot Commands*

*!help* - Show this help
*!chat <message>* - Chat with AI
*!clear* - Clear session
*!session info* - Show session info

Or just send a message to chat directly!
"""
        
        elif cmd == "chat":
            if not args:
                return "Please provide a message. Usage: *!chat <message>*"
            return self._handle_chat(" ".join(args), user_id)
        
        elif cmd == "clear":
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
                return "✅ Session cleared. Starting fresh!"
            return "No active session to clear."
        
        elif cmd == "session":
            session_id = self.user_sessions.get(user_id)
            if session_id:
                return f"📋 *Session Info*\nSession ID: `{session_id}`"
            return "No active session. Start chatting to create one!"
        
        else:
            return f"Unknown command: *{cmd}*. Type *!help* for available commands."
    
    def _handle_chat(self, message: str, user_id: str) -> str:
        """Handle chat with AI"""
        try:
            session_id = self.user_sessions.get(user_id)
            
            response = self.agent.chat(
                user_message=message,
                session_id=session_id,
                use_memory=True
            )
            
            # Save session
            self.user_sessions[user_id] = response["session_id"]
            
            return response["content"]
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return "Sorry, I couldn't process your message. Please try again."
    
    def _send_response(self, to: str, response: str):
        """Send response back to user"""
        # This would be implemented based on your provider
        # For now, just log it
        logger.info(f"Response to {to}: {response[:100]}...")
        
        # In a real implementation, you would:
        # 1. Split long messages if needed
        # 2. Send via your provider (Twilio, etc.)
        # 3. Handle errors and retries
    
    def start(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
        """Start the bridge server"""
        logger.info(f"Starting WhatsApp Bridge on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


# Simple standalone runner
if __name__ == "__main__":
    bridge = WhatsAppBridge()
    bridge.start()
