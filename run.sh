#!/usr/bin/env bash
# 企业级多Agent平台启动脚本
# 用法: bash run.sh

cd "$(dirname "$0")"

echo "================================================"
echo "  企业级多Agent任务执行平台 v2.0"
echo "  DeepSeek + LangGraph + FastAPI"
echo "================================================"

# 检查虚拟环境
if [ -d "venv" ]; then
    source venv/Scripts/activate 2>/dev/null || source venv/bin/activate
    echo "[✓] 虚拟环境已激活"
else
    echo "[!] 未找到虚拟环境，使用系统 Python"
fi

# 安装/更新依赖
echo "[*] 检查依赖..."
pip install -r requirements.txt -q

echo ""
echo "[*] 启动服务: http://localhost:8000"
echo "[*] API文档:  http://localhost:8000/docs"
echo "[*] 按 Ctrl+C 停止服务"
echo ""

# 启动 FastAPI
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
