# 股票監控儀表板

基於多策略技術分析的即時股票監控系統，支援波段交易策略。

## 功能特色

- 📊 即時監控 QQQ、NVDA、VOO 三檔股票
- 🎯 整合式策略控制中心
- 🚦 多策略自動生成買賣信號
- 📈 視覺化圖表顯示價格趨勢和技術指標
- 🔄 每5分鐘自動更新數據
- 📱 響應式設計，支援手機端瀏覽
- 💰 投資組合分析和預期報酬計算

## 核心策略

### 策略1: 20日均線+RSI波段交易
**買入條件:**
- 股價跌破20日簡單移動平均線
- RSI指標 < 30（超賣狀態）

**賣出條件:**
- 股價突破20日簡單移動平均線
- RSI指標 > 70（超買狀態）

### 多策略支援
- 均值回歸策略 (Mean Reversion)
- 動量追蹤策略 (Momentum)
- 買入持有策略 (Buy & Hold)
- 自動策略切換和比較

## 技術架構

- **後端**: Python Flask
- **數據源**: Yahoo Finance (yfinance)
- **前端**: Bootstrap 5 + Chart.js
- **技術指標**: SMA、RSI、MACD 等多種指標
- **策略引擎**: 多策略並行分析

## 安裝與運行

### 環境需求
- Python 3.8+
- pip 套件管理器

### 快速啟動
```bash
# 1. 克隆專案
git clone https://github.com/stanleyoho/stock-monitor.git
cd stock-monitor

# 2. 創建虛擬環境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 啟動應用
python app.py
# 或使用啟動腳本
chmod +x start.sh
./start.sh

# 5. 開啟瀏覽器
# 前往 http://localhost:5000
```

### 項目結構
```
stock-monitor/
├── app.py                 # Flask主應用
├── app_v2.py             # 進階多策略版本
├── config.py              # 配置參數
├── requirements.txt       # Python依賴包
├── start.sh              # 啟動腳本
├── templates/
│   ├── index.html        # 主頁面模板
│   └── index_v2.html     # 進階版模板
├── static/
│   ├── css/              # 樣式文件
│   └── js/               # 前端JavaScript
├── modules/              # 核心模組
│   ├── multi_strategy_engine.py
│   ├── portfolio_manager.py
│   ├── risk_manager.py
│   └── stock_analyzer.py
└── strategies/           # 交易策略
    ├── base_strategy.py
    ├── mean_reversion_strategy.py
    ├── momentum_strategy.py
    └── buy_hold_strategy.py
```

## API端點

### `/api/signals`
獲取即時交易信號
```json
{
    "success": true,
    "data": [
        {
            "symbol": "QQQ",
            "current_price": 450.25,
            "sma_20": 448.50,
            "rsi": 65.2,
            "signal": "HOLD",
            "confidence": 0.75,
            "strategy": "mean_reversion",
            "reasons": ["技術指標分析結果"],
            "timestamp": "2025-08-07T10:30:00"
        }
    ]
}
```

### `/api/portfolio`
獲取投資組合分析

### `/api/strategies`
獲取可用策略列表

## 使用說明

1. **策略控制中心**: 點擊「策略說明」查看當前策略詳情
2. **信號監控**: 查看即時買賣信號和信心度指標
3. **圖表分析**: 互動式價格圖表含技術指標
4. **投資組合**: 查看預期報酬和風險分析

## 注意事項

- 此工具僅供參考，不構成投資建議
- 市場數據可能有延遲
- 投資有風險，請謹慎決策
- 建議結合基本面分析使用

## 貢獻

歡迎提交 Issue 和 Pull Request 來改進這個項目。

## 開發路線圖

查看 [TODO_BACKLOG.md](TODO_BACKLOG.md) 了解計劃中的功能和改進。

---

此工具專為技術分析和波段交易策略設計，幫助投資者追蹤多種技術指標變化並做出明智決策。