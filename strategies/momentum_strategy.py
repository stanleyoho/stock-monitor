"""
動量策略
基於價格動量和技術指標的交易策略
"""

import pandas as pd
from .base_strategy import BaseStrategy
from modules.stock_analyzer import StockAnalyzer, VIXAnalyzer
from utils.constants import SIGNAL_THRESHOLDS, EXPECTED_RETURNS, RISK_MANAGEMENT

class MomentumStrategy(BaseStrategy):
    """動量策略實現"""
    
    def __init__(self):
        super().__init__(
            name="momentum",
            description="基於價格動量、RSI和MACD的動量策略，適合趨勢明確的市場"
        )
        self.risk_level = "high"
        
    def generate_signal(self, analyzer: StockAnalyzer, **kwargs) -> dict:
        """
        生成動量策略信號
        
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
        macd, macd_signal, macd_histogram = analyzer.calculate_macd()
        volume_analysis = analyzer.get_volume_analysis()
        
        if not all([current_price, sma_20 is not None, rsi is not None]):
            return self.format_signal(symbol, 'HOLD', 0.0, ['技術指標計算失敗'])
        
        # 獲取最新數值
        current_sma20 = float(sma_20.iloc[-1])
        current_sma50 = float(sma_50.iloc[-1]) if sma_50 is not None else None
        current_rsi = float(rsi.iloc[-1])
        current_macd = float(macd.iloc[-1]) if macd is not None else None
        current_macd_signal = float(macd_signal.iloc[-1]) if macd_signal is not None else None
        
        # 獲取VIX水平
        vix_level = VIXAnalyzer.get_vix_level()
        
        # 動量信號邏輯
        signal = 'HOLD'
        confidence = 0.5
        reasons = []
        
        # 強勢動量買入條件
        buy_conditions = []
        sell_conditions = []
        
        # 1. 價格相對於移動平均線的位置
        if current_price > current_sma20:
            buy_conditions.append("價格高於20日均線")
            confidence += 0.1
        else:
            sell_conditions.append("價格低於20日均線")
        
        # 2. 移動平均線排列
        if current_sma50 and current_sma20 > current_sma50:
            buy_conditions.append("短期均線高於長期均線")
            confidence += 0.1
        elif current_sma50 and current_sma20 < current_sma50:
            sell_conditions.append("短期均線低於長期均線")
        
        # 3. RSI動量確認
        rsi_thresholds = SIGNAL_THRESHOLDS['RSI']
        if 40 < current_rsi < 70:  # 健康的動量區間
            buy_conditions.append(f"RSI在健康動量區間({current_rsi:.1f})")
            confidence += 0.15
        elif current_rsi < 30:
            buy_conditions.append(f"RSI超賣反彈機會({current_rsi:.1f})")
            confidence += 0.1
        elif current_rsi > 80:
            sell_conditions.append(f"RSI極度超買({current_rsi:.1f})")
            confidence += 0.2
        
        # 4. MACD動量確認
        if current_macd and current_macd_signal:
            if current_macd > current_macd_signal and current_macd > 0:
                buy_conditions.append("MACD金叉且為正值")
                confidence += 0.2
            elif current_macd < current_macd_signal:
                sell_conditions.append("MACD死叉")
                confidence += 0.1
        
        # 5. 成交量確認
        if volume_analysis and volume_analysis['is_high_volume']:
            if len(buy_conditions) > len(sell_conditions):
                buy_conditions.append(f"成交量放大確認({volume_analysis['volume_ratio']:.1f}倍)")
                confidence += 0.15
            else:
                sell_conditions.append(f"高成交量下跌({volume_analysis['volume_ratio']:.1f}倍)")
                confidence += 0.1
        
        # 6. VIX市場情緒調整
        if vix_level:
            vix_thresholds = SIGNAL_THRESHOLDS['VIX']
            if vix_level > vix_thresholds['PANIC']:
                # 市場恐慌，謹慎操作
                if signal == 'BUY':
                    confidence *= 0.7
                    reasons.append(f"VIX恐慌水平({vix_level:.1f})，降低買入信心")
            elif vix_level < vix_thresholds['LOW']:
                # 市場過熱，提高賣出機會
                if len(sell_conditions) > 0:
                    confidence += 0.1
                    reasons.append(f"VIX過低({vix_level:.1f})，市場可能過熱")
        
        # 生成最終信號
        if len(buy_conditions) >= 3 and len(buy_conditions) > len(sell_conditions):
            signal = 'BUY'
            reasons = buy_conditions
        elif len(sell_conditions) >= 2 and len(sell_conditions) > len(buy_conditions):
            signal = 'SELL' 
            reasons = sell_conditions
        else:
            reasons = ["動量信號不明確，保持觀望"]
        
        # 確保信心度在合理範圍內
        confidence = max(0.1, min(1.0, confidence))
        
        # 添加額外數據
        additional_data = {
            'current_price': current_price,
            'sma_20': current_sma20,
            'sma_50': current_sma50,
            'rsi': current_rsi,
            'macd': current_macd,
            'macd_signal': current_macd_signal,
            'vix_level': vix_level,
            'stop_loss_price': self._calculate_stop_loss(symbol, current_price),
            'target_price': self._calculate_target_price(symbol, current_price, signal)
        }
        
        return self.format_signal(symbol, signal, confidence, reasons, additional_data)
    
    def calculate_expected_return(self, symbol: str, current_price: float) -> float:
        """
        計算動量策略的預期報酬率
        
        Args:
            symbol (str): 股票代號
            current_price (float): 當前價格
            
        Returns:
            float: 預期年化報酬率
        """
        # 基礎預期報酬率
        base_return = EXPECTED_RETURNS.get(symbol, 0.08)
        
        # 動量策略通常有更高的預期報酬但也有更高風險
        momentum_multiplier = 1.3
        
        # 根據股票類型調整
        if 'ETF' in symbol or symbol in ['VOO', 'QQQ', 'SPY']:
            # ETF較為穩健
            momentum_multiplier = 1.1
        elif symbol in ['NVDA', 'TSLA']:
            # 高波動股票
            momentum_multiplier = 1.5
        
        return base_return * momentum_multiplier
    
    def _calculate_stop_loss(self, symbol: str, current_price: float) -> float:
        """
        計算停損價格
        
        Args:
            symbol (str): 股票代號
            current_price (float): 當前價格
            
        Returns:
            float: 停損價格
        """
        stop_loss_pct = RISK_MANAGEMENT['STOP_LOSS'].get(symbol, 0.12)
        return current_price * (1 - stop_loss_pct)
    
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
        
        # 根據預期報酬率計算目標價格
        expected_return = self.calculate_expected_return(symbol, current_price)
        target_multiplier = 1 + (expected_return * 0.3)  # 30%的年度預期報酬作為目標
        
        return current_price * target_multiplier