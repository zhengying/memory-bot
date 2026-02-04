#!/usr/bin/env python3
"""
WhatsApp Web 连接 - 类似 OpenClaw 的方式

使用 whatsapp-web.js 或 Baileys 库直接连接 WhatsApp Web，
无需 Twilio 或 WhatsApp Business API 账号。

Usage:
    python whatsapp_web.py
    
    # 首次运行会显示二维码，用手机 WhatsApp 扫描即可连接
"""

import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Callable

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WhatsAppWebClient:
    """
    WhatsApp Web 客户端
    
    使用 Node.js + whatsapp-web.js 实现，类似 OpenClaw 的方式。
    """
    
    def __init__(self, session_name: str = "memory-bot-session"):
        self.session_name = session_name
        self.connected = False
        self.qr_code: Optional[str] = None
        self.user_info: Optional[Dict] = None
        self.message_handlers: List[Callable] = []
        
        # 项目目录
        self.project_dir = Path(__file__).parent
        self.session_dir = self.project_dir / "whatsapp-sessions"
        self.session_dir.mkdir(exist_ok=True)
        
        logger.info(f"📱 WhatsApp Web 客户端初始化")
        logger.info(f"   会话名称: {session_name}")
        logger.info(f"   会话目录: {self.session_dir}")
    
    def on_message(self, handler: Callable[[Dict], None]):
        """注册消息处理器"""
        self.message_handlers.append(handler)
        logger.info(f"✅ 已注册消息处理器: {handler.__name__}")
    
    def connect(self):
        """
        连接到 WhatsApp Web
        
        首次连接会显示二维码，需要用手机扫描。
        """
        logger.info("🚀 开始连接 WhatsApp Web...")
        
        # 检查 Node.js 环境
        if not self._check_nodejs():
            logger.error("❌ 未安装 Node.js，请先安装 Node.js 14+")
            logger.info("   安装指南: https://nodejs.org/")
            return False
        
        # 检查 whatsapp-web.js
        if not self._check_whatsapp_web_js():
            logger.info("📦 安装 whatsapp-web.js...")
            self._install_whatsapp_web_js()
        
        # 创建 Node.js 脚本
        self._create_node_script()
        
        # 启动连接
        self._start_connection()
        
        return True
    
    def _check_nodejs(self) -> bool:
        """检查 Node.js 环境"""
        try:
            result = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"✅ Node.js 已安装: {version}")
                return True
        except Exception as e:
            logger.debug(f"检查 Node.js 失败: {e}")
        return False
    
    def _check_whatsapp_web_js(self) -> bool:
        """检查 whatsapp-web.js 是否安装"""
        node_modules = self.project_dir / "node_modules" / "whatsapp-web.js"
        return node_modules.exists()
    
    def _install_whatsapp_web_js(self):
        """安装 whatsapp-web.js"""
        try:
            logger.info("📦 正在安装 whatsapp-web.js...")
            
            # 创建 package.json
            package_json = self.project_dir / "package.json"
            if not package_json.exists():
                with open(package_json, 'w') as f:
                    json.dump({
                        "name": "memory-bot-whatsapp",
                        "version": "1.0.0",
                        "dependencies": {
                            "whatsapp-web.js": "^1.23.0",
                            "qrcode-terminal": "^0.12.0"
                        }
                    }, f, indent=2)
            
            # 安装依赖
            subprocess.run(
                ['npm', 'install'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            logger.info("✅ whatsapp-web.js 安装完成")
            
        except Exception as e:
            logger.error(f"❌ 安装 whatsapp-web.js 失败: {e}")
            raise
    
    def _create_node_script(self):
        """创建 Node.js 脚本"""
        script_path = self.project_dir / "whatsapp-bridge.js"
        
        script_content = '''
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');

// 配置
const SESSION_NAME = process.env.WHATSAPP_SESSION_NAME || 'memory-bot-session';
const SESSION_DIR = path.join(__dirname, 'whatsapp-sessions');

// 确保会话目录存在
if (!fs.existsSync(SESSION_DIR)) {
    fs.mkdirSync(SESSION_DIR, { recursive: true });
}

// 创建客户端
const client = new Client({
    authStrategy: new LocalAuth({
        dataPath: SESSION_DIR,
        clientId: SESSION_NAME
    }),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

// 生成二维码
client.on('qr', (qr) => {
    console.log('\\n🔐 请扫描二维码以登录 WhatsApp Web:');
    qrcode.generate(qr, { small: true });
    console.log('\\n📱 扫描方法:');
    console.log('   1. 打开手机 WhatsApp');
    console.log('   2. 设置 → 已连接的设备 → 连接设备');
    console.log('   3. 扫描二维码\\n');
});

// 认证成功
client.on('authenticated', () => {
    console.log('✅ WhatsApp 认证成功！');
});

// 认证失败
client.on('auth_failure', (msg) => {
    console.error('❌ 认证失败:', msg);
});

// 就绪
client.on('ready', () => {
    console.log('🚀 WhatsApp Bot 已就绪！');
    console.log('   等待接收消息...');
    console.log('   按 Ctrl+C 退出\\n');
});

// 接收消息
client.on('message', async (msg) => {
    console.log(`📩 收到消息来自 ${msg.from}: ${msg.body}`);
    
    // 忽略自己的消息
    if (msg.fromMe) return;
    
    // 忽略群组消息（可选）
    if (msg.from.includes('@g.us')) {
        console.log('   忽略群组消息');
        return;
    }
    
    // 处理消息
    const response = await processMessage(msg.body, msg.from);
    
    // 发送回复
    await msg.reply(response);
    console.log(`📤 回复: ${response.substring(0, 100)}...`);
});

// 断开连接
client.on('disconnected', (reason) => {
    console.log('⚠️  WhatsApp 断开连接:', reason);
});

// 处理消息
async function processMessage(message, from) {
    // 简单命令处理
    if (message.startsWith('!')) {
        const parts = message.slice(1).split(' ');
        const cmd = parts[0].toLowerCase();
        const args = parts.slice(1);
        
        switch (cmd) {
            case 'help':
                return `🤖 *Memory Bot 帮助*

*!help* - 显示帮助
*!chat <消息>* - 和 AI 聊天
*!clear* - 清除会话
*!info* - 显示会话信息

或直接发送消息聊天！`;
            
            case 'chat':
                if (args.length === 0) {
                    return '请提供消息内容。用法: *!chat <消息>*';
                }
                return `💬 你说: ${args.join(' ')}\\n\\n[AI 回复将在这里]';
            
            case 'clear':
                return '✅ 会话已清除。开始新的对话！';
            
            case 'info':
                return '📋 *会话信息*\\n会话 ID: [会话 ID 将在这里]';
            
            default:
                return `未知命令: *${cmd}*。输入 *!help* 查看可用命令。`;
        }
    }
    
    // 普通消息
    return `收到你的消息: *${message}*\\n\\n我是 Memory Bot，一个会记住事情的 AI 助手。有什么可以帮你的吗？`;
}

// 启动客户端
console.log('🚀 启动 WhatsApp Bridge...');
client.initialize();

// 处理退出
process.on('SIGINT', async () => {
    console.log('\\n🛑 正在关闭...');
    await client.destroy();
    process.exit(0);
});
'''
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        logger.info(f"✅ Node.js 脚本已创建: {script_path}")
    
    def _start_connection(self):
        """启动连接"""
        logger.info("🚀 启动 WhatsApp Bridge...")
        
        try:
            # 启动 Node.js 进程
            self.node_process = subprocess.Popen(
                ['node', 'whatsapp-bridge.js'],
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            logger.info("✅ WhatsApp Bridge 已启动")
            logger.info("   等待二维码扫描...")
            
            # 读取输出
            for line in self.node_process.stdout:
                line = line.strip()
                if line:
                    print(line)
                    
                    # 检测就绪状态
                    if "已就绪" in line or "ready" in line.lower():
                        self.connected = True
                        logger.info("🎉 WhatsApp 连接成功！")
                    
                    # 检测二维码
                    if "二维码" in line or "QR" in line:
                        logger.info("📱 请扫描二维码登录")
            
        except Exception as e:
            logger.error(f"❌ 启动失败: {e}")
            raise
    
    def disconnect(self):
        """断开连接"""
        if hasattr(self, 'node_process') and self.node_process:
            logger.info("🛑 正在断开连接...")
            self.node_process.terminate()
            self.node_process.wait()
            self.connected = False
            logger.info("✅ 已断开连接")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WhatsApp Web 连接工具')
    parser.add_argument('--session', '-s', default='memory-bot-session', help='会话名称')
    parser.add_argument('--no-qr', action='store_true', help='不显示二维码（已登录）')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 WhatsApp Web 连接工具")
    print("=" * 60)
    print()
    
    client = WhatsAppWebClient(session_name=args.session)
    
    try:
        client.connect()
    except KeyboardInterrupt:
        print("\n\n🛑 用户中断")
        client.disconnect()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        client.disconnect()


if __name__ == "__main__":
    main()
