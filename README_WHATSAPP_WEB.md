# WhatsApp Web 集成 - OpenClaw 风格

使用 WhatsApp Web 协议直接连接，无需 Twilio 或 WhatsApp Business API 账号。

## 特点

- ✅ **无需外部账号** - 直接使用你的 WhatsApp 账号
- ✅ **扫码连接** - 像登录 WhatsApp Web 一样简单
- ✅ **持久会话** - 登录一次，长期使用
- ✅ **安全可靠** - 使用官方 WhatsApp Web 协议

## 快速开始

### 1. 安装依赖

需要 Node.js 14+：

```bash
# 检查 Node.js 版本
node --version

# 安装依赖
npm install
```

### 2. 启动连接

```bash
npm start
```

或者：

```bash
node whatsapp-bridge.js
```

### 3. 扫描二维码

首次运行会显示二维码：

```
🔐 请扫描二维码以登录 WhatsApp Web:

█████████████████████████████████
██ ▄▄▄▄▄ █▀█ █▄█ ▄▄▄▄▄ ██▄▄▄▄▄██
██ █   █ █▀▀▀█ ▀ █   █ █ ▄▄▄▄▄██
██ █▄▄▄█ ██▄ ▀▄▀ █▄▄▄█ █ █▄▄▄▄▄█
██▄▄▄▄▄▄▄█ ▀ █ █ █▄▄▄▄▄█▄▄▄▄▄███
██ ▄▄▄ ▄▄  ▄▀█ ▀ ▄▄▄▄▄ ▄▄▄▄▄▄███

📱 扫描方法:
   1. 打开手机 WhatsApp
   2. 设置 → 已连接的设备 → 连接设备
   3. 扫描二维码
```

### 4. 开始使用

扫描成功后显示：

```
✅ WhatsApp 认证成功！
🚀 WhatsApp Bot 已就绪！
   等待接收消息...
   按 Ctrl+C 退出
```

现在你可以：
1. 给朋友发 WhatsApp 消息
2. 收到消息后会自动回复
3. 使用命令如 `!help` 获取帮助

## 命令

| 命令 | 说明 |
|------|------|
| `!help` | 显示帮助信息 |
| `!chat <消息>` | 和 AI 聊天 |
| `!clear` | 清除会话 |
| `!info` | 显示会话信息 |
| 直接发送消息 | 普通聊天 |

## 文件说明

```
memory-bot/
├── whatsapp-bridge.js       # WhatsApp Web 桥接脚本
├── package.json             # Node.js 依赖
├── whatsapp-sessions/       # 会话存储目录
└── README_WHATSAPP_WEB.md   # 本文档
```

## 故障排除

### 1. 二维码不显示

```bash
# 确保终端支持二维码
# 尝试使用不同的终端
# 或者检查 Node.js 版本
node --version  # 需要 14+
```

### 2. 扫描后无法连接

```bash
# 删除会话重新连接
rm -rf whatsapp-sessions
npm start
```

### 3. 依赖安装失败

```bash
# 清理缓存重新安装
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

## 与 Python 集成

如果你想在 Python 中使用 WhatsApp Web：

```python
# 启动 Node.js 桥接
import subprocess

process = subprocess.Popen(
    ['node', 'whatsapp-bridge.js'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

# 读取输出
for line in process.stdout:
    print(line, end='')
```

## 安全提示

⚠️ **重要提示：**

1. **会话文件** - `whatsapp-sessions/` 目录包含敏感信息，不要上传到 GitHub
2. **二维码** - 二维码相当于密码，不要截图分享给他人
3. **登录状态** - 保持登录状态会占用一个 WhatsApp Web 槽位（最多4个）

建议：
- 将 `whatsapp-sessions/` 添加到 `.gitignore`
- 使用专用手机号注册测试账号
- 不在生产环境使用个人 WhatsApp 账号

## 下一步

1. ✅ 测试 WhatsApp Web 连接
2. ✅ 熟悉命令和功能
3. 🔜 集成 AI 回复（OpenAI/Claude）
4. 🔜 添加记忆功能（SQLite/PostgreSQL）
5. 🔜 部署到服务器

有问题？查看完整文档：`README.md`
