#!/bin/bash
# WhatsApp Web QR 码生成脚本

echo "🚀 启动 WhatsApp Web 连接..."
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 未安装 Node.js"
    echo "   请先安装 Node.js 14+: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js 版本: $(node --version)"

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo "❌ 未安装 npm"
    exit 1
fi

echo "✅ npm 版本: $(npm --version)"

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo ""
    echo "📦 正在安装依赖..."
    echo "   这可能需要几分钟（需要下载 Chromium）"
    echo ""
    npm install
    
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
    
    echo "✅ 依赖安装完成"
fi

echo ""
echo "🚀 启动 WhatsApp Web 连接..."
echo ""
echo "📱 准备步骤："
echo "   1. 等待二维码出现"
echo "   2. 打开手机 WhatsApp"
echo "   3. 设置 → 已连接的设备 → 连接设备"
echo "   4. 扫描二维码"
echo ""
echo "⚠️  注意：首次登录需要扫描二维码，之后会自动保持登录"
echo ""

# 启动
node whatsapp-bridge.js
