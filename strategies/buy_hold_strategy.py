"""
買入持有策略
長期投資策略，定期定額與適時加碼
"""

import pandas as pd
from .base_strategy import BaseStrategy
from modules.stock_analyzer import StockAnalyzer, VIXAnalyzer
from modules.risk_manager import RiskManager, StopLossType, TakeProfitType
from utils.constants import SIGNAL_THRESHOLDS, EXPECTED_RETURNS, RISK_MANAGEMENT

class BuyHoldStrategy(BaseStrategy):
    """買入持有策略實現"""
    
    def __init__(self):
        super().__init__(
            name="buy_hold",
            description="長期買入持有策略，重點在適時加碼和風險控制"
        )
        self.risk_level = "low"
        self.risk_manager = RiskManager()
        
    def generate_signal(self, analyzer: StockAnalyzer, **kwargs) -> dict:
        """
        生成買入持有策略信號
        
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
        sma_200 = analyzer.calculate_sma(200)  # 長期趨勢
        rsi = analyzer.calculate_rsi()
        price_change = analyzer.get_price_change(20)  # 20天價格變化
        
        if not all([current_price, sma_20 is not None]):
            return self.format_signal(symbol, 'HOLD', 0.0, ['技術指標計算失敗'])
        
        # 獲取最新數值
        current_sma20 = float(sma_20.iloc[-1])
        # 修復NaN值問題
        try:
            if sma_200 is not None and len(sma_200) > 0:
                sma200_value = float(sma_200.iloc[-1])
                current_sma200 = sma200_value if not pd.isna(sma200_value) else None
            else:
                current_sma200 = None
        except:
            current_sma200 = None
        current_rsi = float(rsi.iloc[-1]) if rsi is not None else 50
        
        # 獲取VIX水平和市場情緒
        vix_level = VIXAnalyzer.get_vix_level()
        market_sentiment = VIXAnalyzer.get_market_sentiment(vix_level) if vix_level else None
        
        # 買入持有策略邏輯
        signal = 'HOLD'  # 預設持有
        confidence = 0.6  # 買入持有策略通常有中等信心
        reasons = []
        
        buy_conditions = []
        reduce_conditions = []
        
        # 1. 基本持有邏輯 - 大部分時間都是持有
        reasons.append("長期投資策略，預設持有")
        
        # 2. 適時加碼條件
        # VIX恐慌加碼
        if vix_level:
            vix_thresholds = SIGNAL_THRESHOLDS['VIX']
            if vix_level > vix_thresholds['PANIC']:
                buy_conditions.append(f"VIX恐慌水平({vix_level:.1f})，絕佳加碼機會")
                confidence += 0.3
                signal = 'BUY'
            elif vix_level > vix_thresholds['HIGH']:
                buy_conditions.append(f"VIX較高({vix_level:.1f})，考慮加碼")
                confidence += 0.2
                signal = 'BUY'
            elif vix_level < vix_thresholds['LOW']:
                # VIX過低，市場可能過熱
                reduce_conditions.append(f"VIX過低({vix_level:.1f})，市場可能過熱")
        
        # 3. 價格大幅回調加碼
        if price_change:
            _, pct_change = price_change
            if pct_change < -10:
                buy_conditions.append(f"20天大幅回調{abs(pct_change):.1f}%，加碼機會")
                confidence += 0.25
                signal = 'BUY'
            elif pct_change < -5:
                buy_conditions.append(f"20天回調{abs(pct_change):.1f}%，小幅加碼")
                confidence += 0.15
                signal = 'BUY'
        
        # 4. RSI超賣加碼
        if current_rsi < 30:
            buy_conditions.append(f"RSI超賣({current_rsi:.1f})，加碼時機")
            confidence += 0.2
            signal = 'BUY'
        elif current_rsi < 35:
            buy_conditions.append(f"RSI偏低({current_rsi:.1f})，可考慮加碼")
            confidence += 0.1
            signal = 'BUY'
        
        # 5. 長期趨勢確認
        if current_sma200:
            if current_price > current_sma200:
                buy_conditions.append("價格高於200日均線，長期趨勢向上")
                confidence += 0.1
            else:
                reduce_conditions.append("價格低於200日均線，長期趨勢轉弱")
                confidence -= 0.1
        
        # 6. 定期定額邏輯（每月15日左右）
        current_date = pd.Timestamp.now()
        if 10 <= current_date.day <= 20:  # 每月中旬定期定額
            buy_conditions.append("定期定額時間")
            if signal != 'BUY':
                signal = 'BUY'
            confidence += 0.1
        
        # 7. 特殊減碼條件（極少觸發）
        extreme_conditions = 0
        if current_rsi > 85:
            extreme_conditions += 1
            reduce_conditions.append(f"RSI極度超買({current_rsi:.1f})")
        
        if price_change:
            _, pct_change = price_change
            if pct_change > 25:  # 20天漲超過25%
                extreme_conditions += 1
                reduce_conditions.append(f"短期漲幅過大({pct_change:.1f}%)")
        
        # 只有在極端條件下才考慮減碼
        if extreme_conditions >= 2:
            signal = 'SELL'
            confidence = 0.4
            reasons = reduce_conditions + ["多個極端條件，考慮適度減碼"]
        elif len(buy_conditions) > 0:
            reasons = buy_conditions
        else:
            reasons = ["持續持有，等待更好的加碼時機"]
        
        # 確保信心度在合理範圍內
        confidence = max(0.2, min(1.0, confidence))
        
        # 計算風險管理方案
        risk_management = None
        if analyzer.data is not None and len(analyzer.data) > 20:
            try:
                # 對於買入持有策略，使用保守的風險管理
                risk_management = self.risk_manager.get_comprehensive_risk_plan(
                    current_price, analyzer.data, 'low'
                )
            except Exception as e:
                print(f"風險管理計算失敗: {e}")
        
        # 添加額外數據，確保沒有NaN值
        additional_data = {
            'current_price': current_price if not pd.isna(current_price) else None,
            'sma_20': current_sma20 if not pd.isna(current_sma20) else None,
            'sma_200': current_sma200,  # 已經處理過NaN
            'rsi': current_rsi if not pd.isna(current_rsi) else None,
            'vix_level': vix_level if vix_level and not pd.isna(vix_level) else None,
            'market_sentiment': market_sentiment['label'] if market_sentiment else None,
            'price_change_20d': price_change[1] if price_change and not pd.isna(price_change[1]) else None,
            'stop_loss_price': None,  # 買入持有策略通常不設停損
            'target_price': None      # 長期持有無特定目標價
        }
        
        return self.format_signal(symbol, signal, confidence, reasons, additional_data, risk_management)
    
    def calculate_expected_return(self, symbol: str, current_price: float) -> float:
        """
        計算買入持有策略的預期報酬率
        
        Args:
            symbol (str): 股票代號
            current_price (float): 當前價格
            
        Returns:
            float: 預期年化報酬率
        """
        # 基礎預期報酬率
        base_return = EXPECTED_RETURNS.get(symbol, 0.08)
        
        # 買入持有策略的預期報酬通常接近市場長期平均
        # 但由於定期定額和恐慌加碼，可能略高於市場平均
        hold_multiplier = 1.1
        
        # 根據股票類型調整
        if symbol in ['VOO', 'SPY']:
            # S&P 500長期表現
            hold_multiplier = 1.0
        elif symbol == 'QQQ':
            # Nasdaq長期成長性較高
            hold_multiplier = 1.05
        elif symbol in ['NVDA', 'TSLA']:
            # 個股的長期持有風險較高，但潛在報酬也較高
            hold_multiplier = 1.2
        elif '.TW' in symbol:
            # 台股長期表現
            hold_multiplier = 0.95
        
        return base_return * hold_multiplier
    
    def get_rebalance_suggestion(self, portfolio_data: dict) -> dict:
        """
        獲取再平衡建議
        
        Args:
            portfolio_data (dict): 投資組合數據
            
        Returns:
            dict: 再平衡建議
        """
        suggestions = {
            'rebalance_needed': False,
            'suggestions': [],
            'reasoning': []
        }
        
        # 買入持有策略的再平衡邏輯較為保守
        # 主要在極端偏離時才建議調整
        
        return suggestions