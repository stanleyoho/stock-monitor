"""
均值回歸策略
基於價格偏離均值時的回歸機會
"""

import pandas as pd
from .base_strategy import BaseStrategy
from modules.stock_analyzer import StockAnalyzer, VIXAnalyzer
from utils.constants import SIGNAL_THRESHOLDS, EXPECTED_RETURNS, RISK_MANAGEMENT

class MeanReversionStrategy(BaseStrategy):
    """均值回歸策略實現"""
    
    def __init__(self):
        super().__init__(
            name="mean_reversion",
            description="基於價格偏離均值的回歸策略，適合震蕩市場和超跌反彈"
        )
        self.risk_level = "medium"
        
    def generate_signal(self, analyzer: StockAnalyzer, **kwargs) -> dict:
        """
        生成均值回歸策略信號
        
        Args:
            analyzer (StockAnalyzer): 股票分析器
            
        Returns:
            dict: 交易信號
        """
        symbol = kwargs.get('symbol', analyzer.symbol)
        
        if analyzer.data is None:
            return self.format_signal(symbol, 'HOLD', 0.0, ['數據獲取失敗'])
        
        # 獲取技術指標
        current_price = analyzer.get_current_price()
        sma_20 = analyzer.calculate_sma(20)
        sma_50 = analyzer.calculate_sma(50)
        rsi = analyzer.calculate_rsi()
        upper_bb, middle_bb, lower_bb = analyzer.calculate_bollinger_bands()
        support_resistance = analyzer.get_support_resistance()
        
        if not all([current_price, sma_20 is not None, rsi is not None]):
            return self.format_signal(symbol, 'HOLD', 0.0, ['技術指標計算失敗'])
        
        # 獲取最新數值
        current_sma20 = float(sma_20.iloc[-1])
        current_sma50 = float(sma_50.iloc[-1]) if sma_50 is not None else None
        current_rsi = float(rsi.iloc[-1])
        
        # 布林帶數值
        current_upper_bb = float(upper_bb.iloc[-1]) if upper_bb is not None else None
        current_middle_bb = float(middle_bb.iloc[-1]) if middle_bb is not None else None
        current_lower_bb = float(lower_bb.iloc[-1]) if lower_bb is not None else None
        
        # 獲取VIX水平
        vix_level = VIXAnalyzer.get_vix_level()
        
        # 均值回歸信號邏輯
        signal = 'HOLD'
        confidence = 0.4
        reasons = []
        
        # 計算價格偏離程度
        price_deviation_sma20 = (current_price - current_sma20) / current_sma20
        if current_sma50:
            price_deviation_sma50 = (current_price - current_sma50) / current_sma50
        else:
            price_deviation_sma50 = 0
        
        buy_conditions = []
        sell_conditions = []
        
        # 1. 基於移動平均線的偏離
        if price_deviation_sma20 < -0.05:  # 價格低於20日均線5%以上
            buy_conditions.append(f"價格較20日均線低{abs(price_deviation_sma20*100):.1f}%")
            confidence += 0.15
        elif price_deviation_sma20 > 0.05:  # 價格高於20日均線5%以上
            sell_conditions.append(f"價格較20日均線高{price_deviation_sma20*100:.1f}%")
            confidence += 0.1
        
        # 2. RSI超買超賣判斷
        rsi_thresholds = SIGNAL_THRESHOLDS['RSI']
        if current_rsi < rsi_thresholds['OVERSOLD']:
            buy_conditions.append(f"RSI超賣({current_rsi:.1f})")
            confidence += 0.2
        elif current_rsi > rsi_thresholds['OVERBOUGHT']:
            sell_conditions.append(f"RSI超買({current_rsi:.1f})")
            confidence += 0.2
        
        # 3. 極端RSI值
        if current_rsi < 20:
            buy_conditions.append(f"RSI極度超賣({current_rsi:.1f})")
            confidence += 0.3
        elif current_rsi > 85:
            sell_conditions.append(f"RSI極度超買({current_rsi:.1f})")
            confidence += 0.3
        
        # 4. 布林帶偏離
        if current_lower_bb and current_upper_bb:
            bb_position = (current_price - current_lower_bb) / (current_upper_bb - current_lower_bb)
            
            if bb_position < 0.1:  # 接近下軌
                buy_conditions.append(f"價格接近布林帶下軌(位置:{bb_position:.1%})")
                confidence += 0.2
            elif bb_position > 0.9:  # 接近上軌
                sell_conditions.append(f"價格接近布林帶上軌(位置:{bb_position:.1%})")
                confidence += 0.15
        
        # 5. 支撐阻力位分析
        if support_resistance:
            distance_to_support = support_resistance['distance_to_support']
            distance_to_resistance = support_resistance['distance_to_resistance']
            
            if distance_to_support < 0.03:  # 接近支撐位3%以內
                buy_conditions.append(f"接近支撐位({distance_to_support:.1%})")
                confidence += 0.15
            elif distance_to_resistance < 0.03:  # 接近阻力位3%以內
                sell_conditions.append(f"接近阻力位({distance_to_resistance:.1%})")
                confidence += 0.1
        
        # 6. VIX恐慌機會
        if vix_level:
            vix_thresholds = SIGNAL_THRESHOLDS['VIX']
            if vix_level > vix_thresholds['HIGH']:
                # 高恐慌時的均值回歸機會
                buy_conditions.append(f"VIX高位恐慌買入機會({vix_level:.1f})")
                confidence += 0.25
            elif vix_level < vix_thresholds['LOW']:
                # 低恐慌時考慮獲利了結
                if current_price > current_sma20:
                    sell_conditions.append(f"VIX低位({vix_level:.1f})，考慮獲利了結")
                    confidence += 0.1
        
        # 7. 連續下跌/上漲天數
        consecutive_days = self._calculate_consecutive_days(analyzer.data)
        if consecutive_days['down'] >= 3:
            buy_conditions.append(f"連續下跌{consecutive_days['down']}天，反彈機會")
            confidence += 0.1
        elif consecutive_days['up'] >= 5:
            sell_conditions.append(f"連續上漲{consecutive_days['up']}天，回調風險")
            confidence += 0.1
        
        # 生成最終信號
        if len(buy_conditions) >= 2 and current_rsi < 40:
            signal = 'BUY'
            reasons = buy_conditions
        elif len(sell_conditions) >= 2 and current_rsi > 60:
            signal = 'SELL'
            reasons = sell_conditions
        else:
            reasons = ["未達到明確的均值回歸信號條件"]
        
        # 確保信心度在合理範圍內
        confidence = max(0.1, min(1.0, confidence))
        
        # 添加額外數據
        additional_data = {
            'current_price': current_price,
            'sma_20': current_sma20,
            'sma_50': current_sma50,
            'rsi': current_rsi,
            'upper_bb': current_upper_bb,
            'middle_bb': current_middle_bb,
            'lower_bb': current_lower_bb,
            'vix_level': vix_level,
            'price_deviation': price_deviation_sma20,
            'stop_loss_price': self._calculate_stop_loss(symbol, current_price),
            'target_price': self._calculate_target_price(symbol, current_price, signal)
        }
        
        return self.format_signal(symbol, signal, confidence, reasons, additional_data)
    
    def calculate_expected_return(self, symbol: str, current_price: float) -> float:
        """
        計算均值回歸策略的預期報酬率
        
        Args:
            symbol (str): 股票代號
            current_price (float): 當前價格
            
        Returns:
            float: 預期年化報酬率
        """
        # 基礎預期報酬率
        base_return = EXPECTED_RETURNS.get(symbol, 0.08)
        
        # 均值回歸策略通常有較穩定的報酬
        reversion_multiplier = 0.9  # 較保守的預期
        
        # 根據股票類型調整
        if 'ETF' in symbol or symbol in ['VOO', 'QQQ', 'SPY']:
            # ETF在震蕩市場中表現穩定
            reversion_multiplier = 1.0
        elif symbol in ['NVDA', 'TSLA']:
            # 高波動股票的均值回歸機會
            reversion_multiplier = 1.1
        
        return base_return * reversion_multiplier
    
    def _calculate_consecutive_days(self, data: pd.DataFrame) -> dict:
        """
        計算連續上漲/下跌天數
        
        Args:
            data (pd.DataFrame): 股票數據
            
        Returns:
            dict: 連續天數信息
        """
        if len(data) < 10:
            return {'up': 0, 'down': 0}
        
        recent_data = data.tail(10)
        price_changes = recent_data['Close'].diff()
        
        consecutive_up = 0
        consecutive_down = 0
        
        # 從最近開始往前計算
        for change in reversed(price_changes.dropna()):
            if change > 0:
                if consecutive_down == 0:
                    consecutive_up += 1
                else:
                    break
            elif change < 0:
                if consecutive_up == 0:
                    consecutive_down += 1
                else:
                    break
            else:
                break  # 價格沒變化
        
        return {'up': consecutive_up, 'down': consecutive_down}
    
    def _calculate_stop_loss(self, symbol: str, current_price: float) -> float:
        """
        計算停損價格
        
        Args:
            symbol (str): 股票代號
            current_price (float): 當前價格
            
        Returns:
            float: 停損價格
        """
        # 均值回歸策略的停損通常較寬
        stop_loss_pct = RISK_MANAGEMENT['STOP_LOSS'].get(symbol, 0.12) * 1.2
        return current_price * (1 - min(stop_loss_pct, 0.20))
    
    def _calculate_target_price(self, symbol: str, current_price: float, signal: str) -> float:
        """
        計算目標價格
        
        Args:
            symbol (str): 股票代號
            current_price (float): 當前價格
            signal (str): 交易信號
            
        Returns:
            float: 目標價格
        """
        if signal != 'BUY':
            return current_price
        
        # 均值回歸的目標通常是回到均值
        expected_return = self.calculate_expected_return(symbol, current_price)
        target_multiplier = 1 + (expected_return * 0.2)  # 較保守的目標
        
        return current_price * target_multiplier