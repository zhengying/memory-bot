# Discord Bot 集成

本模块为 Memory Bot 提供 Discord 集成，允许用户通过 Discord 聊天和命令与 AI 助手交互。

## 功能特性

### 支持的交互方式

1. **前缀命令** - 使用 `!` 前缀发送命令
   - `!help` - 显示帮助信息
   - `!chat <消息>` - 与 AI 聊天
   - `!memory <search|stats>` - 记忆操作
   - `!session <info|list>` - 会话管理
   - `!clear` - 清除当前会话

2. **直接 @提及** - @Bot 直接聊天
   - `@MemoryBot 你好！`
   - 与 AI 进行自然对话

3. **会话管理** - 每个用户有独立的会话
   - 自动维护会话上下文
   - 支持长期记忆检索

## 安装

### 1. 安装依赖

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装 discord.py
pip install discord.py>=2.3.0

# 或添加到项目依赖
# 在 pyproject.toml 的 dependencies 中添加:
# "discord.py>=2.3.0"
```

### 2. 配置环境变量

```bash
# 必需
export DISCORD_TOKEN="your-bot-token-here"

# 可选 (默认值)
export DISCORD_COMMAND_PREFIX="!"
export DISCORD_DESCRIPTION="Memory Bot - AI with long-term memory"
export DISCORD_MAX_MESSAGE_LENGTH="2000"
export DISCORD_DEFAULT_SESSION_TIMEOUT="60"
export DISCORD_LOG_LEVEL="INFO"
```

### 3. 创建 Discord Bot

1. 访问 [Discord Developer Portal](https://discord.com/developers/applications)
2. 点击 "New Application"
3. 输入应用名称，创建
4. 在左侧菜单选择 "Bot"
5. 点击 "Reset Token" 获取 token
6. 开启以下 Privileged Gateway Intents:
   - MESSAGE CONTENT INTENT (必需，用于读取消息内容)
7. 在 "OAuth2" -> "URL Generator":
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Read Message History`, `Read Messages/View Channels`
8. 复制生成的 URL，在浏览器中打开邀请 Bot 加入服务器

## 运行

### 方式 1: 直接运行

```bash
# 在 memory-bot 目录下
python -c "
import asyncio
from core.llm import MockLLMProvider
from core.agent import AgentEngine
from discord_bot import DiscordBot, DiscordConfig

# Setup agent
llm = MockLLMProvider(api_key='test', model='gpt-4')
agent = AgentEngine(llm_provider=llm)

# Load config
config = DiscordConfig()

# Create and start bot
bot = DiscordBot(config=config, agent=agent)
bot.start()
"
```

### 方式 2: 创建启动脚本

创建 `run_discord_bot.py`:

```python
#!/usr/bin/env python3
"""
Discord Bot Launcher
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.llm import MockLLMProvider
from core.agent import AgentEngine
from discord_bot import DiscordBot, DiscordConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    logger.info("Starting Discord Bot...")
    
    try:
        # Setup agent with mock LLM
        # Replace with real LLM provider in production
        llm = MockLLMProvider(api_key='test', model='gpt-4')
        agent = AgentEngine(llm_provider=llm)
        
        # Load config from environment
        config = DiscordConfig()
        
        # Create and start bot
        bot = DiscordBot(config=config, agent=agent)
        
        logger.info(f"Bot configured with prefix: {config.command_prefix}")
        logger.info("Connecting to Discord...")
        
        bot.start()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
```

然后运行:
```bash
chmod +x run_discord_bot.py
./run_discord_bot.py
```

## 测试

运行测试:

```bash
# 运行所有 Discord bot 测试
pytest tests/unit/test_discord_bot.py -v

# 运行特定测试类
pytest tests/unit/test_discord_bot.py::TestDiscordConfig -v

# 运行带覆盖率报告
pytest tests/unit/test_discord_bot.py --cov=discord_bot --cov-report=term-missing
```

## API 参考

### DiscordConfig

配置管理类，从环境变量加载配置。

```python
from discord_bot.config import DiscordConfig

config = DiscordConfig()
print(config.token)        # Bot token
print(config.command_prefix)  # Command prefix (default: "!")
print(config.max_message_length)  # Max message length (default: 2000)
```

### CommandParser

解析 Discord 消息，提取命令和提及。

```python
from discord_bot.commands import CommandParser

parser = CommandParser(prefix="!", bot_id="12345")

# Parse command
result = parser.parse("!chat Hello world")
# result.type = "command"
# result.command = "chat"
# result.args = ["Hello", "world"]

# Parse mention
result = parser.parse("<@12345> Hello bot")
# result.type = "mention"
# result.content = "Hello bot"
```

### CommandHandler

处理并执行命令。

```python
from discord_bot.commands import CommandHandler

handler = CommandHandler(agent=agent_engine)

# Handle command
result = await handler.handle_command(
    command="chat",
    args=["Hello"],
    user_id="123456"
)
# result = {"success": True, "content": "Response text"}
```

### DiscordBot

主 Bot 类，集成所有组件。

```python
from discord_bot import DiscordBot, DiscordConfig
from core.agent import AgentEngine

# Setup
config = DiscordConfig()
agent = AgentEngine(...)

# Create bot
bot = DiscordBot(config=config, agent=agent)

# Start (blocks until stopped)
bot.start()
```

## 故障排除

### Bot 无法接收消息

1. 检查 `MESSAGE CONTENT INTENT` 是否已开启
2. 检查 Bot 是否有 `Read Messages` 权限
3. 检查频道权限设置

### 命令不响应

1. 检查 `DISCORD_TOKEN` 是否正确
2. 检查命令前缀是否正确
3. 查看日志中的错误信息

### 内存/会话不工作

1. 确保 AgentEngine 正确初始化
2. 检查 LLM provider 是否可用
3. 查看 agent 的错误日志

## 许可证

本项目与 memory-bot 使用相同的许可证。