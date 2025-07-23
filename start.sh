#!/bin/bash

# 大模型请求测试工具启动脚本 - 独立版本

echo "🤖 大模型请求测试工具 v1.0.0"
echo "================================"
echo "专业的大模型API测试工具，支持批量测试和结果分析"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3，请先安装 Python"
    exit 1
fi

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  建议在虚拟环境中运行此工具"
    echo "   可以使用: python3 -m venv venv && source venv/bin/activate"
    echo ""
fi

# 安装依赖
echo "📦 安装依赖包..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ 错误: 依赖安装失败"
    exit 1
fi

# 检查配置文件
if [ ! -f "config.py" ]; then
    echo "❌ 错误: 未找到配置文件 config.py"
    exit 1
fi

echo "✅ 配置文件检查通过"
echo "ℹ️  如需修改配置，请编辑 config.py 文件"

echo ""
echo "🚀 启动服务..."
echo "   本地访问: http://localhost:8001"
echo "   按 Ctrl+C 停止服务"
echo ""

# 启动应用
python3 app.py 