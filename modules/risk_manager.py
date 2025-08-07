"""
風險管理模塊
實現停損停利策略計算
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from enum import Enum

class StopLossType(Enum):
    """停損類型"""
    FIXED_PERCENTAGE = "fixed_percentage"  # 固定百分比
    ATR_BASED = "atr_based"  # ATR技術指標
    SUPPORT_RESISTANCE = "support_resistance"  # 支撐阻力位
    TRAILING = "trailing"  # 追蹤停損

class TakeProfitType(Enum):
    """停利類型"""
    FIXED_PERCENTAGE = "fixed_percentage"  # 固定百分比
    RISK_REWARD_RATIO = "risk_reward_ratio"  # 風險報酬比
    FIBONACCI = "fibonacci"  # 費波納契回撤
    TRAILING = "trailing"  # 追蹤停利

class RiskManager:
    """風險管理器"""
    
    def __init__(self):
        self.default_configs = {
            'conservative': {
                'stop_loss_pct': 0.05,  # 5%停損
                'take_profit_pct': 0.10,  # 10%停利
                'trailing_stop_pct': 0.03,  # 3%追蹤停損
                'atr_multiplier': 1.5,
                'risk_reward_ratio': 2.0
            },
            'moderate': {
                'stop_loss_pct': 0.08,  # 8%停損
                'take_profit_pct': 0.15,  # 15%停利
                'trailing_stop_pct': 0.05,  # 5%追蹤停損
                'atr_multiplier': 2.0,
                'risk_reward_ratio': 1.8
            },
            'aggressive': {
                'stop_loss_pct': 0.12,  # 12%停損
                'take_profit_pct': 0.25,  # 25%停利
                'trailing_stop_pct': 0.08,  # 8%追蹤停損
                'atr_multiplier': 2.5,
                'risk_reward_ratio': 1.5
            }
        }
    
    def calculate_stop_loss(self, 
                           current_price: float, 
                           data: pd.DataFrame,
                           stop_type: StopLossType = StopLossType.FIXED_PERCENTAGE,
                           config: str = 'moderate',
                           **kwargs) -> Dict:
        """
        計算停損價格
        
        Args:
            current_price: 當前價格
            data: 股票歷史數據
            stop_type: 停損類型
            config: 風險配置 ('conservative', 'moderate', 'aggressive')
            **kwargs: 其他參數
        
        Returns:
            Dict: 停損信息
        """
        risk_config = self.default_configs[config]
        
        if stop_type == StopLossType.FIXED_PERCENTAGE:
            return self._calculate_fixed_percentage_stop_loss(
                current_price, risk_config['stop_loss_pct']
            )
            
        elif stop_type == StopLossType.ATR_BASED:
            return self._calculate_atr_stop_loss(
                current_price, data, risk_config['atr_multiplier']
            )
            
        elif stop_type == StopLossType.SUPPORT_RESISTANCE:
            return self._calculate_support_resistance_stop_loss(
                current_price, data, kwargs.get('lookback_days', 20)
            )
            
        elif stop_type == StopLossType.TRAILING:
            return self._calculate_trailing_stop_loss(
                current_price, data, risk_config['trailing_stop_pct']
            )
    
    def calculate_take_profit(self, 
                            current_price: float,
                            data: pd.DataFrame,
                            stop_loss_price: float,
                            profit_type: TakeProfitType = TakeProfitType.FIXED_PERCENTAGE,
                            config: str = 'moderate',
                            **kwargs) -> Dict:
        """
        計算停利價格
        
        Args:
            current_price: 當前價格
            data: 股票歷史數據
            stop_loss_price: 停損價格
            profit_type: 停利類型
            config: 風險配置
            **kwargs: 其他參數
        
        Returns:
            Dict: 停利信息
        """
        risk_config = self.default_configs[config]
        
        if profit_type == TakeProfitType.FIXED_PERCENTAGE:
            return self._calculate_fixed_percentage_take_profit(
                current_price, risk_config['take_profit_pct']
            )
            
        elif profit_type == TakeProfitType.RISK_REWARD_RATIO:
            return self._calculate_risk_reward_take_profit(
                current_price, stop_loss_price, risk_config['risk_reward_ratio']
            )
            
        elif profit_type == TakeProfitType.FIBONACCI:
            return self._calculate_fibonacci_take_profit(
                current_price, data, kwargs.get('lookback_days', 50)
            )
            
        elif profit_type == TakeProfitType.TRAILING:
            return self._calculate_trailing_take_profit(
                current_price, data, risk_config['trailing_stop_pct']
            )
    
    def _calculate_fixed_percentage_stop_loss(self, current_price: float, stop_pct: float) -> Dict:
        """固定百分比停損"""
        stop_price = current_price * (1 - stop_pct)
        
        return {
            'type': 'Fixed Percentage',
            'price': stop_price,
            'percentage': stop_pct * 100,
            'distance': current_price - stop_price,
            'description': f'固定{stop_pct*100:.1f}%停損',
            'reasoning': f'當價格跌破{stop_price:.2f}時執行停損'
        }
    
    def _calculate_atr_stop_loss(self, current_price: float, data: pd.DataFrame, multiplier: float) -> Dict:
        """ATR動態停損"""
        if len(data) < 14:
            # 數據不足，使用固定百分比
            return self._calculate_fixed_percentage_stop_loss(current_price, 0.08)
        
        # 計算ATR
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=14).mean().iloc[-1]
        
        stop_price = current_price - (atr * multiplier)
        stop_pct = (current_price - stop_price) / current_price
        
        return {
            'type': 'ATR Based',
            'price': stop_price,
            'percentage': stop_pct * 100,
            'distance': current_price - stop_price,
            'atr_value': atr,
            'multiplier': multiplier,
            'description': f'ATR{multiplier}倍動態停損',
            'reasoning': f'基於{atr:.2f}的ATR值，當價格跌破{stop_price:.2f}時執行停損'
        }
    
    def _calculate_support_resistance_stop_loss(self, current_price: float, data: pd.DataFrame, lookback: int) -> Dict:
        """支撐位停損"""
        if len(data) < lookback:
            return self._calculate_fixed_percentage_stop_loss(current_price, 0.08)
        
        recent_data = data.tail(lookback)
        
        # 找出最近的支撐位（最低點）
        support_levels = []
        for i in range(2, len(recent_data) - 2):
            if (recent_data.iloc[i]['Low'] < recent_data.iloc[i-1]['Low'] and 
                recent_data.iloc[i]['Low'] < recent_data.iloc[i-2]['Low'] and
                recent_data.iloc[i]['Low'] < recent_data.iloc[i+1]['Low'] and 
                recent_data.iloc[i]['Low'] < recent_data.iloc[i+2]['Low']):
                support_levels.append(recent_data.iloc[i]['Low'])
        
        if not support_levels:
            # 沒找到明確支撐位，使用最近低點
            stop_price = recent_data['Low'].min() * 0.98  # 略低於最低點2%
        else:
            # 使用最接近當前價格的支撐位
            support_levels = [s for s in support_levels if s < current_price]
            if support_levels:
                stop_price = max(support_levels) * 0.98  # 略低於支撐位2%
            else:
                stop_price = current_price * 0.92  # 8%停損
        
        stop_pct = (current_price - stop_price) / current_price
        
        return {
            'type': 'Support Level',
            'price': stop_price,
            'percentage': stop_pct * 100,
            'distance': current_price - stop_price,
            'support_levels': len(support_levels),
            'description': f'支撐位停損',
            'reasoning': f'基於技術分析支撐位，當價格跌破{stop_price:.2f}時執行停損'
        }
    
    def _calculate_trailing_stop_loss(self, current_price: float, data: pd.DataFrame, trail_pct: float) -> Dict:
        """追蹤停損"""
        if len(data) < 10:
            return self._calculate_fixed_percentage_stop_loss(current_price, trail_pct)
        
        # 計算最近10天的最高價
        recent_high = data.tail(10)['High'].max()
        
        # 如果當前價格創新高，使用當前價格
        highest_price = max(recent_high, current_price)
        
        stop_price = highest_price * (1 - trail_pct)
        stop_pct = (current_price - stop_price) / current_price
        
        return {
            'type': 'Trailing Stop',
            'price': stop_price,
            'percentage': stop_pct * 100,
            'distance': current_price - stop_price,
            'highest_price': highest_price,
            'trail_percentage': trail_pct * 100,
            'description': f'追蹤停損 {trail_pct*100:.1f}%',
            'reasoning': f'追蹤最高價{highest_price:.2f}，當價格回落{trail_pct*100:.1f}%至{stop_price:.2f}時執行停損'
        }
    
    def _calculate_fixed_percentage_take_profit(self, current_price: float, profit_pct: float) -> Dict:
        """固定百分比停利"""
        profit_price = current_price * (1 + profit_pct)
        
        return {
            'type': 'Fixed Percentage',
            'price': profit_price,
            'percentage': profit_pct * 100,
            'distance': profit_price - current_price,
            'description': f'固定{profit_pct*100:.1f}%停利',
            'reasoning': f'當價格上漲至{profit_price:.2f}時執行停利'
        }
    
    def _calculate_risk_reward_take_profit(self, current_price: float, stop_loss_price: float, ratio: float) -> Dict:
        """風險報酬比停利"""
        risk = current_price - stop_loss_price
        reward = risk * ratio
        profit_price = current_price + reward
        profit_pct = (profit_price - current_price) / current_price
        
        return {
            'type': 'Risk-Reward Ratio',
            'price': profit_price,
            'percentage': profit_pct * 100,
            'distance': profit_price - current_price,
            'ratio': ratio,
            'risk_amount': risk,
            'reward_amount': reward,
            'description': f'風險報酬比 1:{ratio}',
            'reasoning': f'基於停損風險{risk:.2f}，以{ratio}倍報酬比設定停利價{profit_price:.2f}'
        }
    
    def _calculate_fibonacci_take_profit(self, current_price: float, data: pd.DataFrame, lookback: int) -> Dict:
        """費波納契停利"""
        if len(data) < lookback:
            return self._calculate_fixed_percentage_take_profit(current_price, 0.15)
        
        recent_data = data.tail(lookback)
        high_price = recent_data['High'].max()
        low_price = recent_data['Low'].min()
        
        # 計算費波納契回撤位
        price_range = high_price - low_price
        fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
        
        # 如果當前是上升趨勢，使用阻力位作為停利
        if current_price > (high_price + low_price) / 2:
            # 從低點向上計算
            target_levels = [low_price + price_range * (1 + level) for level in fib_levels]
        else:
            # 從高點向下回撤後的反彈目標
            target_levels = [high_price - price_range * level for level in fib_levels]
        
        # 選擇最接近且高於當前價格的目標
        valid_targets = [t for t in target_levels if t > current_price]
        if valid_targets:
            profit_price = min(valid_targets)
        else:
            profit_price = current_price * 1.15
        
        profit_pct = (profit_price - current_price) / current_price
        
        return {
            'type': 'Fibonacci',
            'price': profit_price,
            'percentage': profit_pct * 100,
            'distance': profit_price - current_price,
            'high_price': high_price,
            'low_price': low_price,
            'description': '費波納契停利',
            'reasoning': f'基於費波納契技術分析，目標價位{profit_price:.2f}'
        }
    
    def _calculate_trailing_take_profit(self, current_price: float, data: pd.DataFrame, trail_pct: float) -> Dict:
        """追蹤停利"""
        # 追蹤停利會隨著價格上漲而調整
        initial_target = current_price * 1.15  # 初始15%目標
        
        return {
            'type': 'Trailing Take Profit',
            'price': initial_target,
            'percentage': 15.0,
            'distance': initial_target - current_price,
            'trail_percentage': trail_pct * 100,
            'description': f'追蹤停利 {trail_pct*100:.1f}%',
            'reasoning': f'動態調整停利位，當價格回落{trail_pct*100:.1f}%時執行停利'
        }
    
    def get_comprehensive_risk_plan(self, 
                                  current_price: float,
                                  data: pd.DataFrame,
                                  strategy_risk_level: str = 'moderate') -> Dict:
        """
        獲取全面的風險管理計劃
        
        Args:
            current_price: 當前價格
            data: 股票歷史數據
            strategy_risk_level: 策略風險等級
        
        Returns:
            Dict: 包含多種停損停利方案
        """
        plans = {}
        
        # 方案1: 固定百分比 (保守型)
        stop_loss_1 = self.calculate_stop_loss(
            current_price, data, StopLossType.FIXED_PERCENTAGE, 'conservative'
        )
        take_profit_1 = self.calculate_take_profit(
            current_price, data, stop_loss_1['price'], 
            TakeProfitType.FIXED_PERCENTAGE, 'conservative'
        )
        
        plans['conservative'] = {
            'name': '保守固定百分比',
            'description': '適合新手投資者，風險控制嚴格',
            'stop_loss': stop_loss_1,
            'take_profit': take_profit_1,
            'risk_level': 'low',
            'suitability': '新手、風險承受度低'
        }
        
        # 方案2: ATR動態 (平衡型)
        stop_loss_2 = self.calculate_stop_loss(
            current_price, data, StopLossType.ATR_BASED, strategy_risk_level
        )
        take_profit_2 = self.calculate_take_profit(
            current_price, data, stop_loss_2['price'],
            TakeProfitType.RISK_REWARD_RATIO, strategy_risk_level
        )
        
        plans['balanced'] = {
            'name': 'ATR動態管理',
            'description': '基於市場波動性，動態調整風險',
            'stop_loss': stop_loss_2,
            'take_profit': take_profit_2,
            'risk_level': 'medium',
            'suitability': '有經驗投資者、適應市場波動'
        }
        
        # 方案3: 技術分析 (進階型)
        stop_loss_3 = self.calculate_stop_loss(
            current_price, data, StopLossType.SUPPORT_RESISTANCE, strategy_risk_level
        )
        take_profit_3 = self.calculate_take_profit(
            current_price, data, stop_loss_3['price'],
            TakeProfitType.FIBONACCI, strategy_risk_level
        )
        
        plans['technical'] = {
            'name': '技術分析型',
            'description': '基於支撐阻力位和費波納契分析',
            'stop_loss': stop_loss_3,
            'take_profit': take_profit_3,
            'risk_level': 'medium',
            'suitability': '技術分析愛好者'
        }
        
        # 方案4: 追蹤動態 (積極型)
        stop_loss_4 = self.calculate_stop_loss(
            current_price, data, StopLossType.TRAILING, 'aggressive'
        )
        take_profit_4 = self.calculate_take_profit(
            current_price, data, stop_loss_4['price'],
            TakeProfitType.TRAILING, 'aggressive'
        )
        
        plans['aggressive'] = {
            'name': '追蹤動態型',
            'description': '最大化趨勢利潤，適合趨勢明確時',
            'stop_loss': stop_loss_4,
            'take_profit': take_profit_4,
            'risk_level': 'high',
            'suitability': '經驗豐富、積極投資者'
        }
        
        return {
            'current_price': current_price,
            'timestamp': pd.Timestamp.now().isoformat(),
            'plans': plans,
            'recommendation': self._get_plan_recommendation(plans, strategy_risk_level)
        }
    
    def _get_plan_recommendation(self, plans: Dict, strategy_risk_level: str) -> Dict:
        """根據策略風險等級推薦最適合的方案"""
        if strategy_risk_level == 'low':
            recommended = 'conservative'
        elif strategy_risk_level == 'high':
            recommended = 'aggressive'
        else:
            recommended = 'balanced'
        
        return {
            'recommended_plan': recommended,
            'reason': f'基於{strategy_risk_level}風險等級推薦',
            'alternative': 'technical' if recommended != 'technical' else 'balanced'
        }