#!/bin/bash

echo "🚀 开始Vercel部署流程..."

# 检查是否安装了Vercel CLI
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI未安装，正在安装..."
    npm install -g vercel
fi

# 检查是否已登录
if ! vercel whoami &> /dev/null; then
    echo "🔐 请先登录Vercel..."
    vercel login
fi

# 检查环境变量文件
if [ ! -f "llm.env" ]; then
    echo "⚠️  警告: llm.env文件不存在"
    echo "请在Vercel控制台中设置GEMINI_API_KEY环境变量"
fi

# 部署项目
echo "📦 开始部署..."
vercel --prod

echo "✅ 部署完成！"
echo "📝 请确保在Vercel控制台中设置了GEMINI_API_KEY环境变量"
