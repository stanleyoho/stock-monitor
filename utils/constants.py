"""
股票監控系統常數定義
統一管理所有常數，避免重複定義
"""

# 監控的股票列表
DEFAULT_US_STOCKS = ['QQQ', 'NVDA', 'VOO']
DEFAULT_TW_STOCKS = ['0050.TW', '00878.TW']

# 技術指標參數
TECHNICAL_INDICATORS = {
    'SMA_PERIODS': {
        'SHORT': 10,
        'MEDIUM': 20,
        'LONG': 50,
        'EXTRA_LONG': 200
    },
    'RSI_PERIOD': 14,
    'MACD': {
        'FAST': 12,
        'SLOW': 26,
        'SIGNAL': 9
    },
    'BOLLINGER_BANDS': {
        'PERIOD': 20,
        'STD_DEV': 2
    }
}

# 買賣信號閾值
SIGNAL_THRESHOLDS = {
    'RSI': {
        'OVERSOLD': 30,
        'OVERBOUGHT': 70,
        'EXTREME_OVERSOLD': 20,
        'EXTREME_OVERBOUGHT': 80
    },
    'VIX': {
        'LOW': 15,
        'NORMAL': 20,
        'HIGH': 25,
        'PANIC': 30
    }
}

# Flask應用配置
FLASK_CONFIG = {
    'DEBUG': True,
    'HOST': '127.0.0.1',
    'PORT': 5000
}

# 數據更新間隔
UPDATE_INTERVALS = {
    'SIGNALS': 300,      # 5分鐘
    'PORTFOLIO': 900,    # 15分鐘
    'CHARTS': 1800       # 30分鐘
}

# 股票數據週期
DATA_PERIODS = {
    'SHORT': '1mo',
    'MEDIUM': '3mo', 
    'LONG': '6mo',
    'YEAR': '1y'
}

# 股票顯示名稱映射
STOCK_NAMES = {
    # 美股
    'QQQ': 'Nasdaq ETF',
    'NVDA': '輝達',
    'VOO': 'S&P 500 ETF',
    'SPY': 'S&P 500 ETF',
    'AAPL': '蘋果',
    'MSFT': '微軟',
    'GOOGL': 'Google',
    'TSLA': 'Tesla',
    
    # 台股
    '0050.TW': '台灣50',
    '00878.TW': '國泰永續高股息',
    '0056.TW': '元大高股息',
    '006208.TW': '富邦台50',
    '2330.TW': '台積電'
}

# 投資組合預設配置
DEFAULT_PORTFOLIO_CONFIG = {
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
REBALANCE_CONFIG = {
    'THRESHOLD': 0.08,        # 8%偏離時觸發再平衡
    'ALERT_THRESHOLD': 0.05,  # 5%偏離時提醒
    'MIN_AMOUNT': 100         # 最小調整金額
}

# 風險管理參數
RISK_MANAGEMENT = {
    'STOP_LOSS': {
        # 個股
        'NVDA': 0.15,     # 15%停損
        'TSLA': 0.20,     # 20%停損
        'AAPL': 0.12,     # 12%停損
        'MSFT': 0.12,     # 12%停損
        
        # ETF
        'QQQ': 0.12,      # 12%停損
        'VOO': 0.10,      # 10%停損
        'SPY': 0.10,      # 10%停損
        
        # 台股
        '0050.TW': 0.10,  # 10%停損
        '00878.TW': 0.08, # 8%停損
        '2330.TW': 0.15   # 15%停損
    },
    'POSITION_SIZE': {
        'MAX_INDIVIDUAL_STOCK': 0.30,  # 單一個股最大比例
        'MAX_SECTOR': 0.40,             # 單一板塊最大比例
        'MIN_DIVERSIFICATION': 5        # 最少持股數量
    }
}

# 預期年化報酬率參數
EXPECTED_RETURNS = {
    # 美股
    'VOO': 0.10,      # 10% S&P 500歷史平均
    'SPY': 0.10,      # 10% S&P 500歷史平均
    'QQQ': 0.12,      # 12% Nasdaq歷史平均
    'NVDA': 0.25,     # 25% 高成長股預期
    'AAPL': 0.15,     # 15% 大型科技股
    'MSFT': 0.14,     # 14% 大型科技股
    'TSLA': 0.20,     # 20% 電動車成長股
    
    # 台股
    '0050.TW': 0.08,   # 8% 台股大盤
    '00878.TW': 0.06,  # 6% 高股息ETF
    '0056.TW': 0.06,   # 6% 高股息ETF
    '2330.TW': 0.12    # 12% 台積電
}

# 波動率參數
VOLATILITY = {
    # 美股
    'VOO': 0.16,      # S&P 500
    'SPY': 0.16,      # S&P 500
    'QQQ': 0.20,      # Nasdaq
    'NVDA': 0.45,     # 高波動個股
    'AAPL': 0.25,     # 大型科技股
    'MSFT': 0.23,     # 大型科技股
    'TSLA': 0.50,     # 極高波動
    
    # 台股
    '0050.TW': 0.18,   # 台股大盤
    '00878.TW': 0.12,  # 高股息ETF
    '0056.TW': 0.12,   # 高股息ETF
    '2330.TW': 0.30    # 台積電
}

# 策略類型定義
STRATEGY_TYPES = {
    'MOMENTUM': '動量策略',
    'MEAN_REVERSION': '均值回歸策略', 
    'TREND_FOLLOWING': '趨勢跟隨策略',
    'VALUE_INVESTING': '價值投資策略',
    'GROWTH_INVESTING': '成長投資策略',
    'DIVIDEND_FOCUSED': '股息策略',
    'RISK_PARITY': '風險平價策略',
    'BUY_AND_HOLD': '買入持有策略'
}

# 市場情緒映射
MARKET_SENTIMENT = {
    'EXTREME_GREED': {'vix_max': 12, 'label': '🤑 極度貪婪', 'color': '#00ff00'},
    'GREED': {'vix_max': 15, 'label': '😊 貪婪', 'color': '#32cd32'},
    'NEUTRAL': {'vix_max': 20, 'label': '😐 中性', 'color': '#ffd700'},
    'FEAR': {'vix_max': 25, 'label': '😰 恐懼', 'color': '#ff8c00'},
    'EXTREME_FEAR': {'vix_max': 30, 'label': '😨 極度恐懼', 'color': '#ff4500'},
    'PANIC': {'vix_max': 100, 'label': '🚨 恐慌', 'color': '#dc143c'}
}

# 預設用戶投資組合 (基於你的實際持股)
DEFAULT_USER_PORTFOLIO = {
    'US_STOCKS': {
        'VOO': {'shares': 94, 'avg_cost': 555.38},
        'NVDA': {'shares': 167, 'avg_cost': 163.98},
        'QQQ': {'shares': 25, 'avg_cost': 532.57}
    },
    'TW_STOCKS': {
        '00878.TW': {'shares': 36300, 'avg_cost': 20.83},
        '0050.TW': {'shares': 4900, 'avg_cost': 47.92}
    }
}