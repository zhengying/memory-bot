#!/usr/bin/env python3
"""
简化版 WhatsApp Bot 测试
无需安装复杂依赖，直接测试核心流程
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleAgent:
    """简化版 Agent，无需外部依赖"""
    
    def __init__(self):
        self.sessions = {}
        self.memory = []
        logger.info("✅ SimpleAgent 初始化完成")
    
    def chat(self, user_message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """模拟 AI 回复"""
        
        # 创建或获取会话
        if not session_id:
            session_id = f"session_{datetime.now().timestamp()}"
        
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        # 保存用户消息
        self.sessions[session_id].append({
            "role": "user",
            "content": user_message,
            "time": datetime.now().isoformat()
        })
        
        # 生成模拟回复
        response = self._generate_response(user_message)
        
        # 保存助手回复
        self.sessions[session_id].append({
            "role": "assistant",
            "content": response,
            "time": datetime.now().isoformat()
        })
        
        return {
            "content": response,
            "session_id": session_id,
            "tokens_used": len(user_message) + len(response),
        }
    
    def _generate_response(self, message: str) -> str:
        """生成模拟回复"""
        message = message.lower()
        
        if "你好" in message or "hi" in message or "hello" in message:
            return "你好！我是 Memory Bot。我可以帮你记住事情、回答问题。试试对我说些什么！"
        
        elif "帮助" in message or "help" in message:
            return """🤖 *Memory Bot 帮助*

我可以做：
• 陪你聊天
• 记住你说的事情
• 回答你的问题

命令：
• !help - 显示帮助
• !clear - 清除会话
• 直接发送消息即可聊天

有什么想问的吗？"""
        
        elif "记住" in message or "memory" in message:
            return "好的，我会记住这个。我的记忆功能正在开发中，以后会更强大！"
        
        elif "名字" in message or "name" in message:
            return "我是 Memory Bot，一个会记住事情的 AI 助手。你呢？"
        
        elif "?" in message or "什么" in message or "怎么" in message:
            return "这是个好问题！作为 AI 助手，我会尽力帮你找到答案。你能多告诉我一些背景吗？"
        
        else:
            return f"收到：*{message}*\n\n我还在学习中，但我会记住我们的对话。有什么我可以帮你的吗？"


class SimpleWhatsAppBot:
    """简化版 WhatsApp Bot"""
    
    def __init__(self):
        self.agent = SimpleAgent()
        self.user_sessions = {}
        logger.info("✅ SimpleWhatsAppBot 初始化完成")
    
    def process_message(self, phone: str, message: str) -> str:
        """处理消息"""
        logger.info(f"处理消息: {phone} -> {message[:50]}...")
        
        # 简单命令处理
        if message.startswith('!'):
            return self._handle_command(message, phone)
        
        # 普通聊天
        return self._handle_chat(message, phone)
    
    def _handle_command(self, command: str, user_id: str) -> str:
        """处理命令"""
        parts = command[1:].split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd == "help":
            return """
🤖 *Memory Bot 命令*

*!help* - 显示帮助
*!chat <消息>* - 和 AI 聊天
*!clear* - 清除会话
*!info* - 显示会话信息

或直接发送消息聊天！
"""
        
        elif cmd == "chat":
            if not args:
                return "请提供消息内容。用法: *!chat <消息>*"
            return self._handle_chat(" ".join(args), user_id)
        
        elif cmd == "clear":
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
                return "✅ 会话已清除。开始新的对话！"
            return "没有活动会话需要清除。"
        
        elif cmd == "info":
            session_id = self.user_sessions.get(user_id)
            if session_id:
                return f"📋 *会话信息*\n会话 ID: `{session_id}`"
            return "没有活动会话。开始聊天来创建一个！"
        
        else:
            return f"未知命令: *{cmd}*。输入 *!help* 查看可用命令。"
    
    def _handle_chat(self, message: str, user_id: str) -> str:
        """处理聊天"""
        session_id = self.user_sessions.get(user_id)
        
        response = self.agent.chat(
            user_message=message,
            session_id=session_id
        )
        
        # 保存会话
        self.user_sessions[user_id] = response["session_id"]
        
        return response["content"]


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Memory Bot - 简化版 WhatsApp 测试")
    print("=" * 60)
    print("\n✅ 无需安装依赖")
    print("✅ 无需外部账户")
    print("✅ 纯本地测试")
    print("\n" + "=" * 60)
    
    # 创建 Bot
    bot = SimpleWhatsAppBot()
    
    # 测试用户
    test_users = [
        "+8613800138000",
        "+8613900139000",
    ]
    
    print("\n预设测试用户:")
    for i, user in enumerate(test_users, 1):
        print(f"  {i}. {user}")
    print()
    
    # 交互循环
    while True:
        try:
            user_input = input("📱 输入 (手机号 消息，或 'quit'): ").strip()
            
            if user_input.lower() == 'quit':
                print("\n👋 再见！")
                break
            
            # 解析输入
            parts = user_input.split(' ', 1)
            if len(parts) < 2:
                print("❌ 格式: 手机号 消息\n")
                continue
            
            phone, message = parts
            
            # 处理
            print("\n" + "-" * 60)
            response = bot.process_message(phone, message)
            print("-" * 60)
            print(f"\n📤 回复:\n{response}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}\n")


if __name__ == "__main__":
    main()
