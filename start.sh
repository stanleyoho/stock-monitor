#!/bin/bash

# 股票監控應用啟動腳本

echo "🚀 啟動股票監控儀表板..."

# 檢查虛擬環境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 虛擬環境不存在，正在創建..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 安裝依賴包..."
    pip install flask yfinance pandas numpy requests plotly
else
    echo "✅ 虛擬環境已存在，激活中..."
    source venv/bin/activate
fi

echo "🌐 啟動Web服務器 (http://localhost:5000)"
echo "💡 使用 Ctrl+C 停止服務器"
echo "📊 正在載入股票數據，請稍候..."

python app.py