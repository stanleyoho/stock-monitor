"""
股票分析器模組
提供股票數據獲取和技術指標計算功能
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Optional, Tuple
from utils.constants import TECHNICAL_INDICATORS, DATA_PERIODS
from utils.error_handler import (
    handle_exceptions, DataFetchError, safe_execute,
    safe_get_price, safe_calculate_indicator
)

class StockAnalyzer:
    """股票分析器類"""
    
    def __init__(self, symbol: str):
        """
        初始化股票分析器
        
        Args:
            symbol (str): 股票代號
        """
        self.symbol = symbol
        self.data: Optional[pd.DataFrame] = None
        
    @handle_exceptions(error_context="股票數據獲取", default_return=False)
    def fetch_data(self, period: str = 'medium') -> bool:
        """
        獲取股票數據
        
        Args:
            period (str): 數據週期 ('short', 'medium', 'long', 'year')
            
        Returns:
            bool: 是否成功獲取數據
        """
        if not self.symbol or not isinstance(self.symbol, str):
            raise DataFetchError(self.symbol, "無效的股票代號")
        
        period_mapping = DATA_PERIODS
        # 將period轉換為大寫以匹配常數
        period_key = period.upper()
        actual_period = period_mapping.get(period_key, period_mapping['MEDIUM'])
        
        ticker = yf.Ticker(self.symbol)
        data = ticker.history(period=actual_period)
        
        if data.empty:
            raise DataFetchError(self.symbol, f"無法獲取 {period} 期間的數據")
        
        # 驗證數據完整性
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise DataFetchError(self.symbol, f"數據缺失必要欄位: {missing_columns}")
        
        self.data = data
        return True
    
    def calculate_sma(self, window: int = None, period: str = 'medium') -> Optional[pd.Series]:
        """
        計算簡單移動平均線
        
        Args:
            window (int): 移動平均週期，如果為None則使用預設
            period (str): 使用預設週期 ('short', 'medium', 'long', 'extra_long')
            
        Returns:
            pd.Series: SMA數值
        """
        if self.data is None:
            return None
            
        if window is None:
            window_mapping = TECHNICAL_INDICATORS['SMA_PERIODS']
            window = window_mapping.get(period.upper(), window_mapping['MEDIUM'])
            
        return self.data['Close'].rolling(window=window).mean()
    
    def calculate_rsi(self, window: int = None) -> Optional[pd.Series]:
        """
        計算RSI指標
        
        Args:
            window (int): RSI計算週期
            
        Returns:
            pd.Series: RSI數值
        """
        if self.data is None:
            return None
            
        if window is None:
            window = TECHNICAL_INDICATORS['RSI_PERIOD']
            
        close_prices = self.data['Close']
        delta = close_prices.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, fast: int = None, slow: int = None, signal: int = None) -> Tuple[Optional[pd.Series], Optional[pd.Series], Optional[pd.Series]]:
        """
        計算MACD指標
        
        Args:
            fast (int): 快線週期
            slow (int): 慢線週期  
            signal (int): 信號線週期
            
        Returns:
            Tuple: (MACD線, 信號線, 直方圖)
        """
        if self.data is None:
            return None, None, None
            
        macd_config = TECHNICAL_INDICATORS['MACD']
        if fast is None:
            fast = macd_config['FAST']
        if slow is None:
            slow = macd_config['SLOW']
        if signal is None:
            signal = macd_config['SIGNAL']
            
        close_prices = self.data['Close']
        exp1 = close_prices.ewm(span=fast).mean()
        exp2 = close_prices.ewm(span=slow).mean()
        
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return macd, signal_line, histogram
    
    def calculate_bollinger_bands(self, period: int = None, std_dev: float = None) -> Tuple[Optional[pd.Series], Optional[pd.Series], Optional[pd.Series]]:
        """
        計算布林帶
        
        Args:
            period (int): 計算週期
            std_dev (float): 標準差倍數
            
        Returns:
            Tuple: (上軌, 中軌, 下軌)
        """
        if self.data is None:
            return None, None, None
            
        bb_config = TECHNICAL_INDICATORS['BOLLINGER_BANDS']
        if period is None:
            period = bb_config['PERIOD']
        if std_dev is None:
            std_dev = bb_config['STD_DEV']
            
        close_prices = self.data['Close']
        middle_band = close_prices.rolling(window=period).mean()
        std = close_prices.rolling(window=period).std()
        
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return upper_band, middle_band, lower_band
    
    def calculate_volume_sma(self, window: int = 20) -> Optional[pd.Series]:
        """
        計算成交量移動平均
        
        Args:
            window (int): 移動平均週期
            
        Returns:
            pd.Series: 成交量SMA
        """
        if self.data is None:
            return None
            
        return self.data['Volume'].rolling(window=window).mean()
    
    def get_current_price(self) -> Optional[float]:
        """
        獲取當前價格
        
        Returns:
            float: 當前價格
        """
        if self.data is None or self.data.empty:
            return None
        return float(self.data['Close'].iloc[-1])
    
    def get_price_change(self, periods: int = 1) -> Optional[Tuple[float, float]]:
        """
        獲取價格變化
        
        Args:
            periods (int): 比較的週期數
            
        Returns:
            Tuple: (絕對變化, 百分比變化)
        """
        if self.data is None or len(self.data) < periods + 1:
            return None
            
        current_price = self.data['Close'].iloc[-1]
        previous_price = self.data['Close'].iloc[-(periods + 1)]
        
        absolute_change = current_price - previous_price
        percentage_change = (absolute_change / previous_price) * 100
        
        return float(absolute_change), float(percentage_change)
    
    def get_volume_analysis(self) -> Optional[dict]:
        """
        獲取成交量分析
        
        Returns:
            dict: 成交量分析結果
        """
        if self.data is None:
            return None
            
        current_volume = self.data['Volume'].iloc[-1]
        avg_volume = self.data['Volume'].rolling(window=20).mean().iloc[-1]
        
        return {
            'current_volume': int(current_volume),
            'average_volume': int(avg_volume),
            'volume_ratio': float(current_volume / avg_volume) if avg_volume > 0 else 0,
            'is_high_volume': current_volume > avg_volume * 1.5
        }
    
    def get_support_resistance(self, lookback_periods: int = 20) -> Optional[dict]:
        """
        獲取支撐阻力位
        
        Args:
            lookback_periods (int): 回望週期
            
        Returns:
            dict: 支撐阻力位信息
        """
        if self.data is None or len(self.data) < lookback_periods:
            return None
            
        recent_data = self.data.tail(lookback_periods)
        
        resistance = float(recent_data['High'].max())
        support = float(recent_data['Low'].min())
        current_price = float(self.data['Close'].iloc[-1])
        
        return {
            'resistance': resistance,
            'support': support,
            'current_price': current_price,
            'distance_to_resistance': (resistance - current_price) / current_price,
            'distance_to_support': (current_price - support) / current_price
        }

class VIXAnalyzer:
    """VIX恐慌指數分析器"""
    
    @staticmethod
    def get_vix_level() -> Optional[float]:
        """
        獲取當前VIX水平
        
        Returns:
            float: VIX數值
        """
        try:
            vix_ticker = yf.Ticker("^VIX")
            vix_data = vix_ticker.history(period="5d")
            if not vix_data.empty:
                return float(vix_data['Close'].iloc[-1])
        except:
            pass
        return None
    
    @staticmethod
    def get_market_sentiment(vix_level: float) -> dict:
        """
        根據VIX水平判斷市場情緒
        
        Args:
            vix_level (float): VIX數值
            
        Returns:
            dict: 市場情緒信息
        """
        from utils.constants import MARKET_SENTIMENT
        
        for sentiment, config in MARKET_SENTIMENT.items():
            if vix_level <= config['vix_max']:
                return {
                    'sentiment': sentiment,
                    'label': config['label'],
                    'color': config['color'],
                    'vix_level': vix_level
                }
        
        return {
            'sentiment': 'UNKNOWN',
            'label': '❓ 未知',
            'color': '#808080',
            'vix_level': vix_level
        }