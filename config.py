# 股票監控應用配置文件

# 監控的股票列表
STOCKS = ['QQQ', 'NVDA', 'VOO']

# 台股ETF (用於完整投資組合分析)  
TW_STOCKS = ['0050.TW', '00878.TW']

# 技術指標參數
SMA_PERIOD = 20  # 簡單移動平均線週期
RSI_PERIOD = 14  # RSI指標週期
MACD_FAST = 12   # MACD快線
MACD_SLOW = 26   # MACD慢線
MACD_SIGNAL = 9  # MACD信號線

# 買賣信號閾值
RSI_OVERSOLD = 30   # RSI超賣閾值
RSI_OVERBOUGHT = 70 # RSI超買閾值
VIX_PANIC_LEVEL = 30  # VIX恐慌閾值

# Flask應用配置
FLASK_DEBUG = True
FLASK_HOST = '127.0.0.1'
FLASK_PORT = 5000

# 數據更新間隔（秒）
UPDATE_INTERVAL = 300  # 5分鐘

# 股票數據週期
DATA_PERIOD = '3mo'  # 3個月歷史數據

# 股票顯示名稱映射
STOCK_NAMES = {
    'QQQ': 'Nasdaq ETF',
    'NVDA': '輝達',
    'VOO': 'S&P 500 ETF',
    '0050.TW': '台灣50',
    '00878.TW': '國泰永續高股息'
}

# 投資組合配置 (基於用戶現有持股)
PORTFOLIO_CONFIG = {
    'US_STOCKS': {
        'VOO': {'target_weight': 0.55, 'type': 'etf', 'risk_level': 'low'},
        'NVDA': {'target_weight': 0.30, 'type': 'individual', 'risk_level': 'high'},
        'QQQ': {'target_weight': 0.15, 'type': 'etf', 'risk_level': 'medium'}
    },
    'TW_STOCKS': {
        '00878.TW': {'target_weight': 0.75, 'type': 'etf', 'risk_level': 'low'},
        '0050.TW': {'target_weight': 0.25, 'type': 'etf', 'risk_level': 'medium'}
    }
}

# 動態平衡閾值
REBALANCE_THRESHOLD = 0.08  # 8%偏離時觸發再平衡
REBALANCE_ALERT_THRESHOLD = 0.05  # 5%偏離時提醒

# 風險管理參數
STOP_LOSS = {
    'NVDA': 0.15,  # 15%停損
    'QQQ': 0.12,   # 12%停損
    'VOO': 0.10,   # 10%停損
    '0050.TW': 0.10,
    '00878.TW': 0.08
}

# 預期年化報酬率 (用於推算)
EXPECTED_RETURNS = {
    'VOO': 0.10,    # 10% S&P 500歷史平均
    'QQQ': 0.12,    # 12% Nasdaq歷史平均
    'NVDA': 0.25,   # 25% 高成長股預期
    '0050.TW': 0.08,  # 8% 台股大盤
    '00878.TW': 0.06   # 6% 高股息ETF
}

# 波動率參數 (用於風險計算)
VOLATILITY = {
    'VOO': 0.16,
    'QQQ': 0.20,
    'NVDA': 0.45,
    '0050.TW': 0.18,
    '00878.TW': 0.12
}