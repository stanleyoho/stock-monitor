# 股票監控儀表板

基於策略1（20日均線+RSI波段交易）的即時股票監控系統。

## 功能特色

- 📊 即時監控 QQQ、NVDA、VOO 三檔股票
- 🚦 自動生成買賣信號（基於20日均線+RSI策略）
- 📈 互動式價格圖表
- 🔄 每5分鐘自動更新
- 📱 響應式設計，支援手機瀏覽

## 策略1說明

### 買入條件（同時滿足）
- 股價跌破20日均線
- RSI < 30 (超賣狀態)

### 賣出條件（同時滿足）
- 股價突破20日均線
- RSI > 70 (超買狀態)

## 安裝與使用

### 快速啟動（推薦）
```bash
cd stock-monitor
./start.sh
```

### 手動安裝步驟

#### 1. 環境需求
- Python 3.8+
- pip

#### 2. 創建虛擬環境
```bash
cd stock-monitor
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows
```

#### 3. 安裝依賴
```bash
pip install -r requirements.txt
```

#### 4. 運行應用
```bash
python app.py
```

#### 5. 瀏覽器訪問
打開瀏覽器，訪問 `http://localhost:5000`

### 使用說明
- 📊 頁面會自動載入QQQ、NVDA、VOO三檔股票的即時數據
- 🚦 根據策略1自動生成買賣信號
- 🔄 每5分鐘自動更新數據
- 📈 點擊股票卡片查看詳細圖表
- ⌨️ 按 Ctrl+R 手動刷新數據

## API 端點

- `/api/signals` - 獲取所有股票交易信號
- `/api/stock/<symbol>` - 獲取特定股票詳細數據

## 技術架構

- **後端**: Flask + yfinance
- **前端**: Bootstrap 5 + Chart.js
- **數據源**: Yahoo Finance
- **技術指標**: 自行計算SMA、RSI

## 注意事項

- 此工具僅供參考，不構成投資建議
- 市場數據可能有延遲
- 投資有風險，請謹慎決策

## 開發者

此工具是為波段交易策略量身定制，幫助追蹤技術指標變化。