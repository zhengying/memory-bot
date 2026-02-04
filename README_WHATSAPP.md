# WhatsApp Bot for Memory Bot

This module provides WhatsApp integration for Memory Bot, allowing users to interact with the AI assistant through WhatsApp messages.

## Features

- 📱 **WhatsApp Messaging**: Send and receive messages via WhatsApp
- 🧠 **Long-term Memory**: Access to the same memory system as Discord bot
- 💬 **Session Management**: Persistent chat sessions across conversations
- ⚡ **Command Support**: Same commands as Discord bot (!help, !chat, !memory, etc.)
- 🔐 **Owner Controls**: Admin commands restricted to configured owners

## Installation

### Prerequisites

1. Python 3.10+
2. A WhatsApp Business API account (Twilio recommended) OR
3. WhatsApp Web session (for development/testing)

### Install Dependencies

```bash
pip install -e ".[whatsapp]"
```

Or install Twilio directly:
```bash
pip install twilio>=8.0.0
```

## Configuration

Create a `.env` file or set environment variables:

### Required Settings

```bash
# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER=+1234567890  # Your WhatsApp number

# For Twilio Integration
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=+14155238886  # Twilio sandbox number
```

### Optional Settings

```bash
# Bot Configuration
WHATSAPP_COMMAND_PREFIX=!
WHATSAPP_OWNER_NUMBERS=+1234567890,+0987654321
WHATSAPP_MAX_MESSAGE_LENGTH=4000
WHATSAPP_DEFAULT_SESSION_TIMEOUT=60
WHATSAPP_LOG_LEVEL=INFO

# Auto-reply mode (respond to all messages)
WHATSAPP_AUTO_REPLY=false
```

## Usage

### Running the WhatsApp Bot

```python
from whatsapp_bot import WhatsAppBot
from core.agent import AgentEngine
from core.llm import OpenAIProvider

# Initialize agent
llm = OpenAIProvider(api_key="your-api-key")
agent = AgentEngine(llm_provider=llm)

# Create and start bot
bot = WhatsAppBot(agent=agent)
bot.start()
```

Or use the CLI:
```bash
python -m whatsapp_bot
```

### Available Commands

| Command | Description |
|---------|-------------|
| `!help` | Show help message |
| `!chat <message>` | Chat with AI |
| `!memory search <query>` | Search your memory |
| `!memory stats` | Show memory statistics |
| `!session info` | Show current session info |
| `!clear` | Clear current session |

### Example Conversations

**Direct message:**
```
User: Hello!
Bot: Hello! How can I help you today?
```

**Using commands:**
```
User: !chat What is machine learning?
Bot: Machine learning is a subset of artificial intelligence...
```

**Memory search:**
```
User: !memory search Python
Bot: 🔍 Searching memory for: `Python`

(Found 3 memories...)
```

## WhatsApp Integration Methods

### 1. Twilio (Recommended for Production)

Twilio provides a reliable WhatsApp Business API integration:

1. Sign up at [Twilio](https://www.twilio.com/)
2. Activate WhatsApp sandbox or apply for business number
3. Configure webhook URL to your bot endpoint
4. Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWATSAPP_NUMBER`

**Advantages:**
- Reliable message delivery
- Official WhatsApp Business API
- Supports media messages
- Good for production

**Limitations:**
- Requires business verification for production
- Costs per message

### 2. WhatsApp Web (Development/Testing)

For development, you can use WhatsApp Web automation:

**Advantages:**
- Free to use
- Easy to set up for testing

**Limitations:**
- Not suitable for production
- Requires phone to be online
- May violate WhatsApp ToS

### 3. WhatsApp Business API (Direct)

For large-scale deployments, use the official WhatsApp Business API directly through Meta.

## Development

### Project Structure

```
whatsapp_bot/
├── __init__.py          # Module exports
├── config.py            # Configuration management
├── bot.py               # Main bot class
├── commands.py          # Command parsing and handling
└── adapters/            # Platform adapters (optional)
    ├── __init__.py
    ├── base.py          # Base adapter interface
    ├── twilio.py        # Twilio adapter
    └── whatsapp_web.py  # WhatsApp Web adapter
```

### Running Tests

```bash
pytest tests/whatsapp/ -v
```

### Adding New Commands

1. Add command handler in `CommandHandler` class:

```python
async def _handle_mynewcommand(self, args: List[str], user_id: str) -> Dict[str, Any]:
    return {
        "success": True,
        "content": "My new command response!"
    }
```

2. Add to command map in `__init__`:

```python
self.command_map = {
    # ... existing commands
    "mynewcommand": self._handle_mynewcommand,
}
```

## Troubleshooting

### Common Issues

**1. Bot not receiving messages**
- Check webhook URL is correctly configured
- Verify Twilio/WhatsApp credentials
- Check firewall/network settings

**2. Messages not sending**
- Verify phone number format (+countrycode)
- Check message length limits
- Review Twilio logs for errors

**3. Session not persisting**
- Check session timeout settings
- Verify storage backend is working
- Review logs for session errors

**4. QR code not scanning**
- Ensure good lighting for camera
- Clean phone camera lens
- Try refreshing QR code
- Check phone internet connection

### Debug Mode

Enable debug logging:

```bash
export WHATSAPP_LOG_LEVEL=DEBUG
python -m whatsapp_bot
```

### Getting Help

- Check logs: `tail -f logs/whatsapp_bot.log`
- Review Twilio console: https://www.twilio.com/console
- Open an issue on GitHub

## License

This module is part of the Memory Bot project and follows the same license.