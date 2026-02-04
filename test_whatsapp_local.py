#!/usr/bin/env python3
"""
WhatsApp Bot - 本地测试版本（无需外部账户）

这个脚本让你可以在本地测试 WhatsApp Bot 的所有功能，
无需 Twilio 或 WhatsApp Business API 账户。

测试方式：
1. 直接调用函数模拟消息收发
2. 使用简单的 HTTP API 模拟 webhook
3. 查看日志了解处理流程

Usage:
    python test_whatsapp_local.py
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
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


class MockWhatsAppClient:
    """
    模拟 WhatsApp 客户端
    
    替代真实的 Twilio 或 WhatsApp Business API，
    用于本地测试所有功能。
    """
    
    def __init__(self):
        self.messages_sent = []
        self.messages_received = []
        logger.info("✅ MockWhatsAppClient 初始化完成")
    
    def send_message(self, to: str, body: str) -> Dict[str, Any]:
        """
        模拟发送消息
        
        实际不会发送到真正的 WhatsApp，
        而是记录到日志和内存中供查看。
        """
        message = {
            "id": f"mock_msg_{len(self.messages_sent)}",
            "to": to,
            "body": body,
            "status": "sent",
            "timestamp": datetime.now().isoformat()
        }
        self.messages_sent.append(message)
        
        logger.info(f"📤 [模拟发送] 发送到: {to}")
        logger.info(f"   内容: {body[:100]}...")
        
        return message
    
    def receive_message(self, from_number: str, body: str) -> Dict[str, Any]:
        """
        模拟接收消息
        
        用于测试，可以手动触发模拟用户发送消息。
        """
        message = {
            "id": f"mock_recv_{len(self.messages_received)}",
            "from": from_number,
            "body": body,
            "timestamp": datetime.now().isoformat()
        }
        self.messages_received.append(message)
        
        logger.info(f"📥 [模拟接收] 来自: {from_number}")
        logger.info(f"   内容: {body}")
        
        return message
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "messages_sent": len(self.messages_sent),
            "messages_received": len(self.messages_received),
            "total_messages": len(self.messages_sent) + len(self.messages_received)
        }


class LocalWhatsAppBot:
    """
    本地 WhatsApp Bot
    
    使用 MockWhatsAppClient 替代真实的 WhatsApp API，
    让你可以在本地测试所有功能。
    """
    
    def __init__(self):
        logger.info("🚀 初始化本地 WhatsApp Bot...")
        
        # 初始化 Mock 客户端
        self.whatsapp = MockWhatsAppClient()
        
        # 初始化 Agent（使用 Mock LLM）
        self._init_agent()
        
        # 用户会话管理
        self.user_sessions: Dict[str, str] = {}
        
        logger.info("✅ 本地 WhatsApp Bot 初始化完成！")
        logger.info("   使用 Mock 模式，无需外部账户")
        logger.info("   可以安全地测试所有功能")
    
    def _init_agent(self):
        """初始化 Agent"""
        try:
            from core.llm.mock import MockLLMProvider
            from core.agent import AgentEngine
            
            logger.info("🧠 初始化 Mock LLM...")
            llm = MockLLMProvider(api_key="test", model="gpt-4")
            self.agent = AgentEngine(llm_provider=llm)
            logger.info("✅ Agent 初始化完成")
            
        except Exception as e:
            logger.error(f"❌ Agent 初始化失败: {e}")
            raise
    
    def simulate_incoming_message(self, phone_number: str, message: str):
        """
        模拟接收消息
        
        用于测试，模拟用户发送消息到 Bot。
        
        Args:
            phone_number: 发送者手机号 (如: +8613800138000)
            message: 消息内容
        """
        logger.info("=" * 60)
        logger.info(f"📥 模拟收到消息")
        logger.info(f"   来自: {phone_number}")
        logger.info(f"   内容: {message}")
        logger.info("=" * 60)
        
        # 记录接收
        self.whatsapp.receive_message(phone_number, message)
        
        # 处理消息
        response = self._process_message(phone_number, message)
        
        # 发送回复
        self._send_response(phone_number, response)
        
        logger.info("=" * 60)
    
    def _process_message(self, phone_number: str, message: str) -> str:
        """处理消息"""
        try:
            # 简单命令处理
            if message.startswith('!'):
                return self._handle_command(message, phone_number)
            
            # 普通聊天
            return self._handle_chat(message, phone_number)
            
        except Exception as e:
            logger.error(f"❌ 处理消息失败: {e}")
            return "抱歉，处理消息时出错。请重试。"
    
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
        try:
            session_id = self.user_sessions.get(user_id)
            
            response = self.agent.chat(
                user_message=message,
                session_id=session_id,
                use_memory=True
            )
            
            # 保存会话
            self.user_sessions[user_id] = response["session_id"]
            
            return response["content"]
            
        except Exception as e:
            logger.error(f"聊天失败: {e}")
            return "抱歉，我现在无法回复。请稍后再试。"
    
    def _send_response(self, phone_number: str, response: str):
        """发送回复"""
        logger.info(f"📤 准备发送回复到: {phone_number}")
        
        # 使用 Mock 客户端发送
        self.whatsapp.send_message(phone_number, response)
        
        logger.info(f"   回复内容: {response[:100]}...")
    
    def run_interactive_test(self):
        """运行交互式测试"""
        print("\n" + "=" * 60)
        print("🚀 本地 WhatsApp Bot 交互式测试")
        print("=" * 60)
        print("\n这是模拟测试模式，无需真实 WhatsApp 账户。\n")
        print("用法:")
        print("  1. 输入手机号和消息来模拟接收消息")
        print("  2. 查看控制台输出了解处理流程")
        print("  3. 输入 'quit' 退出")
        print("=" * 60 + "\n")
        
        # 预设测试用户
        test_users = [
            "+8613800138000",
            "+8613900139000",
        ]
        
        print("预设测试用户:")
        for i, user in enumerate(test_users, 1):
            print(f"  {i}. {user}")
        print()
        
        while True:
            try:
                # 获取手机号
                phone_input = input("📱 手机号 (直接输入数字或选择 1/2，quit 退出): ").strip()
                
                if phone_input.lower() == 'quit':
                    print("\n👋 再见！")
                    break
                
                # 处理选择
                if phone_input in ['1', '2']:
                    phone_number = test_users[int(phone_input) - 1]
                elif phone_input.startswith('+'):
                    phone_number = phone_input
                else:
                    phone_number = '+86' + phone_input
                
                # 获取消息
                message = input("💬 消息: ").strip()
                
                if not message:
                    print("❌ 消息不能为空\n")
                    continue
                
                # 模拟接收消息
                print("\n" + "-" * 60)
                self.simulate_incoming_message(phone_number, message)
                print("-" * 60 + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}\n")


def main():
    """主函数"""
    bot = LocalWhatsAppBot()
    bot.run_interactive_test()


if __name__ == "__main__":
    main()
