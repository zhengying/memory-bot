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
    console.log('\n🔐 请扫描二维码以登录 WhatsApp Web:');
    qrcode.generate(qr, { small: true });
    console.log('\n📱 扫描方法:');
    console.log('   1. 打开手机 WhatsApp');
    console.log('   2. 设置 → 已连接的设备 → 连接设备');
    console.log('   3. 扫描二维码\n');
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
    console.log('   按 Ctrl+C 退出\n');
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
                return `💬 你说: ${args.join(' ')}

[AI 回复将在这里]`;
            
            case 'clear':
                return '✅ 会话已清除。开始新的对话！';
            
            case 'info':
                return '📋 *会话信息*
会话 ID: [会话 ID 将在这里]';
            
            default:
                return `未知命令: *${cmd}*。输入 *!help* 查看可用命令。`;
        }
    }
    
    // 普通消息
    return `收到你的消息: *${message}*

我是 Memory Bot，一个会记住事情的 AI 助手。有什么可以帮你的吗？`;
}

// 启动客户端
console.log('🚀 启动 WhatsApp Bridge...');
client.initialize();

// 处理退出
process.on('SIGINT', async () => {
    console.log('\n🛑 正在关闭...');
    await client.destroy();
    process.exit(0);
});
