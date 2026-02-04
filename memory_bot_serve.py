#!/usr/bin/env python3
"""
Memory-Bot Serve - OpenClaw 风格的服务启动器

Usage:
    # 使用默认配置启动
    python memory_bot_serve.py
    
    # 使用自定义配置文件
    python memory_bot_serve.py --config channels.yaml
    
    # 仅启用特定渠道
    python memory_bot_serve.py --channels whatsapp

Features:
    - 纯配置驱动，无需代码
    - 支持多渠道（WhatsApp、Discord、Telegram）
    - 支持 Mock 模式（无需 API Key 测试）
    - 热重载配置
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    """配置管理"""
    
    def __init__(self, config_path: str = "channels.yaml"):
        self.config_path = config_path
        self.data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        import yaml
        
        if not os.path.exists(self.config_path):
            logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
            return self._default_config()
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 替换环境变量
        config = self._expand_env_vars(config)
        
        return config
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            "server": {"host": "0.0.0.0", "port": 5000},
            "channels": {
                "whatsapp": {"enabled": True, "provider": "mock"},
                "discord": {"enabled": False},
                "telegram": {"enabled": False}
            },
            "ai": {"provider": "mock"},
            "memory": {"enabled": True}
        }
    
    def _expand_env_vars(self, obj: Any) -> Any:
        """递归替换环境变量"""
        if isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # 支持 ${VAR} 和 $VAR 格式
            import re
            pattern = r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)'
            
            def replace_var(match):
                var_name = match.group(1) or match.group(2)
                return os.getenv(var_name, match.group(0))
            
            return re.sub(pattern, replace_var, obj)
        return obj
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        keys = key.split('.')
        value = self.data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value


class MockChannel:
    """模拟渠道（用于测试）"""
    
    def __init__(self, config: Config):
        self.config = config
        self.messages = []
    
    def start(self):
        """启动模拟渠道"""
        logger.info("🎭 启动 Mock 渠道（测试模式）")
        logger.info("   无需外部账户即可测试")
        self._run_interactive_mode()
    
    def _run_interactive_mode(self):
        """运行交互模式"""
        print("\n" + "=" * 60)
        print("🚀 Memory-Bot 交互式测试")
        print("=" * 60)
        print("\n提示：")
        print("  - 输入手机号和消息来模拟发送")
        print("  - 输入 'quit' 退出")
        print("  - 预设测试用户: +8613800138000")
        print("=" * 60 + "\n")
        
        while True:
            try:
                user_input = input("💬 输入 (手机号 消息，或 'quit'): ").strip()
                
                if user_input.lower() == 'quit':
                    print("\n👋 再见！")
                    break
                
                # 解析输入
                parts = user_input.split(' ', 1)
                if len(parts) < 2:
                    print("❌ 格式: 手机号 消息\n")
                    continue
                
                phone, message = parts
                
                # 处理消息
                self._process_message(phone, message)
                
            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}\n")
    
    def _process_message(self, phone: str, message: str):
        """处理消息"""
        logger.info(f"处理消息: {phone} -> {message[:50]}...")
        
        # 这里可以调用 agent 处理
        # 简化版本，直接返回固定回复
        response = f"收到你的消息: *{message}*\n\n[这是 Mock 回复，实际部署后会使用 AI 回复]"
        
        logger.info(f"回复: {response[:100]}...")
        print(f"\n📤 回复给 {phone}:\n{response}\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Memory-Bot Serve - OpenClaw 风格服务启动器'
    )
    parser.add_argument(
        '--config', '-c',
        default='channels.yaml',
        help='配置文件路径 (默认: channels.yaml)'
    )
    parser.add_argument(
        '--channels',
        help='启用的渠道，逗号分隔 (如: whatsapp,discord)'
    )
    parser.add_argument(
        '--mock', '-m',
        action='store_true',
        help='使用 Mock 模式（无需外部账户）'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        help='服务端口'
    )
    
    args = parser.parse_args()
    
    # 加载配置
    config = Config(args.config)
    
    # 应用命令行参数
    if args.mock:
        logger.info("🎭 启用 Mock 模式")
        # 覆盖配置
        config.data['channels']['whatsapp']['provider'] = 'mock'
        config.data['ai']['provider'] = 'mock'
    
    if args.port:
        config.data['server']['port'] = args.port
    
    # 显示配置摘要
    print("\n" + "=" * 60)
    print("🚀 Memory-Bot Serve")
    print("=" * 60)
    print(f"\n配置:")
    print(f"  配置文件: {args.config}")
    print(f"  服务地址: {config.get('server.host')}:{config.get('server.port')}")
    print(f"  AI 提供商: {config.get('ai.provider')}")
    print(f"\n渠道:")
    for channel, settings in config.get('channels', {}).items():
        enabled = settings.get('enabled', False)
        status = "✅ 启用" if enabled else "❌ 禁用"
        print(f"  {channel}: {status}")
    print("=" * 60 + "\n")
    
    # 启动服务
    if args.mock or config.get('channels.whatsapp.provider') == 'mock':
        # 启动 Mock 渠道（交互式）
        mock = MockChannel(config)
        mock.start()
    else:
        # 启动真实服务（需要配置）
        logger.info("启动服务...")
        # 这里会启动 Flask 服务
        # 暂时用 Mock 代替
        logger.warning("真实服务模式需要配置 Twilio，暂时切换到 Mock 模式")
        mock = MockChannel(config)
        mock.start()


if __name__ == "__main__":
    main()
