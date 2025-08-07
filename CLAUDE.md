# CLAUDE.md - Stock Monitor

This file provides guidance to Claude Code when working with the Stock Monitor application.

## Project Overview

Stock Monitor是一個基於Python Flask的股票技術分析監控系統，專門用於執行波段交易策略。該應用監控QQQ、NVDA、VOO三檔股票，並根據20日移動平均線和RSI指標自動生成買賣信號。

## Architecture & Technology Stack

### Backend
- **Framework**: Flask 3.1.1
- **Data Source**: Yahoo Finance (via yfinance library)
- **Technical Analysis**: 自行實現SMA、RSI計算
- **Dependencies**: pandas, numpy, requests

### Frontend
- **Framework**: Bootstrap 5 + Chart.js
- **UI Components**: 響應式儀表板設計
- **Real-time Updates**: JavaScript每5分鐘自動更新
- **Charts**: Line charts for price and technical indicators

### Core Components
```
stock-monitor/
├── app.py              # Flask主應用，包含API endpoints
├── config.py           # 配置參數
├── templates/index.html # 前端主頁面
├── static/
│   ├── css/style.css   # 自定義樣式
│   └── js/app.js       # 前端邏輯和圖表
└── start.sh            # 啟動腳本
```

## Trading Strategy Implementation

### Strategy 1: 20-Day SMA + RSI Band Trading
此應用實現的核心策略，基於技術分析的波段交易方法：

**買入信號條件 (同時滿足):**
- 股價跌破20日簡單移動平均線 (SMA20)
- RSI指標 < 30 (超賣狀態)

**賣出信號條件 (同時滿足):**
- 股價突破20日簡單移動平均線 (SMA20)  
- RSI指標 > 70 (超買狀態)

**持有信號:**
- 不滿足買入或賣出條件的所有其他情況

### Technical Indicators Calculation

#### Simple Moving Average (SMA20)
```python
def calculate_sma(self, window=20):
    return self.data['Close'].rolling(window=window).mean()
```

#### RSI (Relative Strength Index)
```python
def calculate_rsi(self, window=14):
    close_prices = self.data['Close']
    delta = close_prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
```

## API Endpoints

### `/api/signals`
**Method**: GET
**Purpose**: 獲取所有監控股票的即時交易信號
**Response**:
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
            "reason": "價格:450.25, SMA20:448.50, RSI:65.2 - 無明確信號",
            "timestamp": "2025-08-07T10:30:00"
        }
    ],
    "timestamp": "2025-08-07T10:30:00"
}
```

### `/api/stock/<symbol>`
**Method**: GET
**Purpose**: 獲取特定股票的詳細歷史數據和圖表信息
**Parameters**: symbol (QQQ, NVDA, VOO)
**Response**: 包含歷史價格、技術指標數據和圖表繪製所需的時間序列數據

## Configuration Parameters

### Key Settings in `config.py`
- `STOCKS = ['QQQ', 'NVDA', 'VOO']` - 監控的股票代號
- `SMA_PERIOD = 20` - 移動平均線週期
- `RSI_PERIOD = 14` - RSI計算週期
- `RSI_OVERSOLD = 30` - RSI超賣閾值
- `RSI_OVERBOUGHT = 70` - RSI超買閾值
- `UPDATE_INTERVAL = 300` - 前端自動更新間隔(秒)
- `DATA_PERIOD = '3mo'` - 獲取歷史數據週期

## Development Workflow

### Adding New Stocks
1. 在`config.py`中的`STOCKS`列表添加股票代號
2. 在`STOCK_NAMES`中添加對應的顯示名稱
3. 前端會自動為新股票創建對應的圖表容器

### Implementing New Strategies
1. 在`StockAnalyzer`類中添加新的計算方法
2. 在`get_trading_signal()`中實現新的信號邏輯
3. 更新前端顯示邏輯以支援新的信號類型

### Adding New Technical Indicators
1. 在`StockAnalyzer`類中實現指標計算方法
2. 修改API返回格式包含新指標數據
3. 更新前端圖表配置顯示新指標

## Environment Setup

### Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### Running the Application
```bash
# Quick start
./start.sh

# Manual start
source venv/bin/activate
python app.py
```

### Development Server
- **URL**: http://localhost:5000
- **Debug Mode**: Enabled by default
- **Hot Reload**: Flask development server supports hot reload

## Frontend Architecture

### JavaScript Class Structure
- `StockMonitor`: 主要的前端控制類
- Methods:
  - `loadSignals()`: 載入交易信號
  - `loadCharts()`: 創建股票圖表
  - `createChart()`: Chart.js圖表創建
  - `startAutoUpdate()`: 自動更新邏輯

### UI Components
- **Signal Cards**: 顯示即時買賣信號的卡片
- **Stock Charts**: 價格走勢和技術指標圖表
- **Strategy Info**: 策略說明和風險提醒
- **Auto Refresh**: 每5分鐘自動更新機制

## Data Flow

1. **Backend**: yfinance獲取Yahoo Finance股票數據
2. **Processing**: 計算SMA20和RSI技術指標
3. **Signal Generation**: 根據策略1邏輯生成買賣信號
4. **API Response**: JSON格式返回給前端
5. **Frontend Rendering**: 更新UI顯示和圖表
6. **Auto Update**: 定時重新執行整個流程

## Future Enhancement Ideas

### Potential Features to Add
1. **多策略支援**: 實現策略2-4的其他買賣策略
2. **Email/SMS通知**: 買賣信號觸發時發送通知
3. **歷史回測**: 策略歷史表現分析
4. **風險管理**: 停損停利自動計算
5. **更多技術指標**: MACD, Bollinger Bands等
6. **Portfolio管理**: 投資組合整體分析
7. **市場恐慌指標**: VIX整合和市場情緒分析

### Performance Optimizations
1. **數據緩存**: Redis緩存股票數據
2. **WebSocket**: 實時數據推送
3. **數據庫**: 存儲歷史信號和回測數據
4. **CDN**: 靜態資源CDN加速

## Error Handling & Logging

### Current Implementation
- API錯誤返回standardized JSON格式
- 前端顯示用戶友好的錯誤信息
- Console logging用於開發調試

### Recommended Enhancements
- 添加Python logging module
- 實現錯誤報告和監控
- 數據獲取失敗時的重試機制

## Security Considerations

- 使用虛擬環境隔離依賴
- 不包含任何敏感信息或API金鑰
- 純讀取操作，不執行實際交易
- 本地運行，無需對外暴露服務

## Testing Strategy

### Manual Testing Checklist
- [ ] 股票數據正確獲取
- [ ] 技術指標計算準確
- [ ] 買賣信號邏輯正確
- [ ] 前端圖表顯示正常
- [ ] 自動更新功能運作
- [ ] 響應式設計適配

### Automated Testing Recommendations
- 單元測試技術指標計算
- API endpoint測試
- 前端UI自動化測試

## Monitoring & Maintenance

### Health Checks
- API endpoints響應時間
- 數據獲取成功率
- 前端載入錯誤率

### Regular Maintenance
- 依賴包更新
- 股票列表檢查
- 策略參數調優

## Development Roadmap & Todo List

### 🎯 Strategy Optimization (策略優化)
- [ ] **策略2實現**: 價值回歸策略 - VIX恐慌指數整合，市場恐慌時調整持股比例
- [ ] **策略3實現**: 動量追蹤策略 - 連續新高加碼，跌破支撐減碼
- [ ] **策略4實現**: 對沖保護策略 - 月線季線重新平衡，獲利了結機制
- [ ] **多時間框架分析**: 日線、週線、月線多重確認
- [ ] **技術指標擴充**: MACD、布林帶、威廉指標、KDJ
- [ ] **自適應參數**: 根據市場波動率調整SMA和RSI週期
- [ ] **策略回測功能**: 歷史數據回測，計算策略勝率和報酬率
- [ ] **策略組合**: 多策略權重分配和信號整合

### 📊 User Experience Enhancement (用戶體驗優化)
- [ ] **買賣信號通知**: Email、SMS、推播通知系統
- [ ] **歷史信號記錄**: 信號觸發歷史、成功率統計
- [ ] **自定義股票監控**: 允許用戶添加/移除監控股票
- [ ] **投資組合管理**: 持股追蹤、損益計算、資產配置
- [ ] **預警系統**: 自定義價格預警、技術指標預警
- [ ] **交易筆記**: 買賣決策記錄和反思功能
- [ ] **市場日曆**: 財報日期、除權息日期提醒
- [ ] **風險管理工具**: 停損停利計算器、倉位管理建議

### 🔧 Technical Optimization (技術優化)
- [ ] **數據緩存系統**: Redis緩存減少API調用
- [ ] **WebSocket即時更新**: 替代定時輪詢的即時推送
- [ ] **數據庫整合**: PostgreSQL存儲歷史數據和用戶設定
- [ ] **API優化**: 並行數據獲取、錯誤重試機制
- [ ] **性能監控**: 響應時間監控、錯誤追蹤
- [ ] **移動端PWA**: Progressive Web App支援離線使用
- [ ] **Docker容器化**: 簡化部署和環境管理
- [ ] **CI/CD pipeline**: 自動化測試和部署

### 📈 Advanced Analytics (進階分析功能)
- [ ] **波動率分析**: 歷史波動率、隱含波動率比較
- [ ] **相關性分析**: 股票間相關係數分析
- [ ] **市場情緒指標**: VIX、Put/Call ratio整合
- [ ] **資金流向分析**: 大單追蹤、主力進出分析
- [ ] **基本面數據**: PE、PB、ROE等基本面指標整合
- [ ] **新聞情感分析**: 新聞標題情感分析影響股價
- [ ] **選擇權數據**: 選擇權未平倉、最大痛點分析
- [ ] **ETF持股分析**: ETF成分股變化追蹤

### 🎨 UI/UX Improvements (界面改進)
- [ ] **深色模式**: 夜間模式支援
- [ ] **可自定義儀表板**: 用戶可調整圖表佈局
- [ ] **圖表互動增強**: 縮放、標註、技術線繪製
- [ ] **響應式優化**: 更好的手機端體驗
- [ ] **多語言支援**: 英文/中文界面切換
- [ ] **快捷鍵支援**: 鍵盤快捷操作
- [ ] **主題客製化**: 顏色主題、字體大小調整
- [ ] **無障礙功能**: 螢幕閱讀器支援、高對比模式

### 🔒 Security & Compliance (安全性與合規)
- [ ] **用戶認證系統**: 登入、註冊、權限管理
- [ ] **數據加密**: 敏感數據加密存儲
- [ ] **API Rate Limiting**: 防止濫用的頻率限制
- [ ] **審計日誌**: 用戶操作記錄和追蹤
- [ ] **免責聲明**: 法律免責條款和風險提醒
- [ ] **數據隱私**: GDPR合規、數據刪除權
- [ ] **SSL憑證**: HTTPS安全連接
- [ ] **輸入驗證**: XSS、SQL注入防護

### 🧪 Testing & Quality Assurance (測試與品質保證)
- [ ] **單元測試**: 技術指標計算準確性測試
- [ ] **整合測試**: API端點功能測試
- [ ] **前端測試**: UI自動化測試
- [ ] **性能測試**: 負載測試、壓力測試
- [ ] **數據驗證**: 股票數據準確性驗證
- [ ] **回歸測試**: 新功能不影響現有功能
- [ ] **用戶驗收測試**: 真實用戶使用反饋
- [ ] **代碼覆蓋率**: 測試覆蓋率目標90%+

### 📦 Deployment & DevOps (部署與維運)
- [ ] **雲端部署**: AWS/Azure/GCP部署選項
- [ ] **負載均衡**: 高可用性架構設計
- [ ] **監控告警**: 系統健康度監控
- [ ] **日誌管理**: 集中化日誌收集分析
- [ ] **備份策略**: 數據備份和災難恢復
- [ ] **版本管理**: 滾動更新、回滾機制
- [ ] **環境分離**: 開發、測試、生產環境
- [ ] **文檔維護**: API文檔、部署文檔更新

### 🎓 Learning & Research (學習與研究功能)
- [ ] **交易教學**: 技術分析教學模組
- [ ] **策略說明**: 互動式策略教學
- [ ] **模擬交易**: 虛擬資金練習交易
- [ ] **市場研究**: 行業分析、市場趨勢報告
- [ ] **交易心理**: 情緒管理、紀律訓練
- [ ] **專家分析**: 專業分析師觀點整合
- [ ] **學習進度**: 用戶學習歷程追蹤
- [ ] **社群功能**: 用戶交流、策略分享

---

## Priority Matrix

### 🚨 High Priority (立即實作)
1. 策略2-4實現 (完成核心功能)
2. 買賣信號通知 (提升實用性)
3. 歷史信號記錄 (數據追蹤)

### ⚡ Medium Priority (近期實作)
1. 自定義股票監控 (用戶客製化)
2. 數據緩存系統 (性能提升)
3. WebSocket即時更新 (技術升級)

### 🎯 Low Priority (長期規劃)
1. 移動端PWA (擴大使用場景)
2. 進階分析功能 (專業功能)
3. 社群功能 (用戶黏性)

---

## Quick Reference

### Start Development
```bash
cd stock-monitor
source venv/bin/activate
python app.py
# Open http://localhost:5000
```

### Add New Stock
1. Edit `config.py`: Add to `STOCKS` and `STOCK_NAMES`
2. Frontend will auto-generate UI components

### Modify Strategy
1. Edit `StockAnalyzer.get_trading_signal()` method
2. Update signal thresholds in `config.py`
3. Test with different market conditions