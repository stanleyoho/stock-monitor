"""
多策略引擎
管理多個交易策略並提供策略比較功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Optional
from modules.stock_analyzer import StockAnalyzer
from modules.portfolio_manager import PortfolioManager
from modules.signal_filter import SignalFilter
from strategies.base_strategy import StrategyManager
from strategies.momentum_strategy import MomentumStrategy
from strategies.mean_reversion_strategy import MeanReversionStrategy
from strategies.buy_hold_strategy import BuyHoldStrategy
from utils.constants import DEFAULT_US_STOCKS, DEFAULT_TW_STOCKS

class MultiStrategyEngine:
    """多策略交易引擎"""
    
    def __init__(self, monitored_stocks: Dict = None):
        """
        初始化多策略引擎
        
        Args:
            monitored_stocks (Dict): 監控的股票 {'US': [...], 'TW': [...]}
        """
        self.strategy_manager = StrategyManager()
        self.portfolio_manager = PortfolioManager()
        self.signal_filter = SignalFilter(
            cooldown_hours=4,              # 4小時冷卻期
            min_confidence_threshold=0.6,  # 60%最低信心度
            signal_confirmation_required=True  # 需要信號確認
        )
        
        # 設置監控股票
        if monitored_stocks is None:
            self.monitored_stocks = {
                'US': DEFAULT_US_STOCKS.copy(),
                'TW': DEFAULT_TW_STOCKS.copy()
            }
        else:
            self.monitored_stocks = monitored_stocks
        
        # 註冊所有可用策略
        self._register_strategies()
        
        # 設置預設活躍策略
        self.strategy_manager.set_active_strategy('momentum')
    
    def _register_strategies(self):
        """註冊所有可用策略"""
        strategies = [
            MomentumStrategy(),
            MeanReversionStrategy(),
            BuyHoldStrategy()
        ]
        
        for strategy in strategies:
            self.strategy_manager.register_strategy(strategy)
    
    def get_available_strategies(self) -> Dict[str, Dict]:
        """
        獲取所有可用策略信息
        
        Returns:
            Dict: 策略信息字典
        """
        strategies = self.strategy_manager.get_all_strategies()
        result = {}
        
        for name, strategy in strategies.items():
            result[name] = {
                'name': strategy.name,
                'description': strategy.description,
                'risk_level': getattr(strategy, 'risk_level', 'medium'),
                'is_active': name == self.strategy_manager.active_strategy
            }
        
        return result
    
    def switch_strategy(self, strategy_name: str) -> bool:
        """
        切換活躍策略
        
        Args:
            strategy_name (str): 策略名稱
            
        Returns:
            bool: 是否成功切換
        """
        return self.strategy_manager.set_active_strategy(strategy_name)
    
    def generate_signals_all_stocks(self, strategy_name: str = None) -> Dict:
        """
        為所有監控股票生成信號
        
        Args:
            strategy_name (str): 指定策略名稱，None則使用活躍策略
            
        Returns:
            Dict: 所有股票的交易信號
        """
        if strategy_name and not self.strategy_manager.set_active_strategy(strategy_name):
            strategy_name = self.strategy_manager.active_strategy
        
        active_strategy = self.strategy_manager.get_active_strategy()
        if not active_strategy:
            return {'error': '沒有可用的策略'}
        
        all_signals = []
        all_symbols = self.monitored_stocks['US'] + self.monitored_stocks['TW']
        
        for symbol in all_symbols:
            try:
                analyzer = StockAnalyzer(symbol)
                if analyzer.fetch_data():
                    raw_signal = active_strategy.generate_signal(analyzer, symbol=symbol)
                    
                    # 應用信號過濾器
                    should_emit, filter_reason = self.signal_filter.should_emit_signal(symbol, raw_signal)
                    
                    if should_emit:
                        # 信號通過過濾
                        final_signal = raw_signal.copy()
                        final_signal['filtered'] = False
                        final_signal['filter_reason'] = 'Signal passed all filters'
                    else:
                        # 信號被過濾
                        final_signal = raw_signal.copy()
                        final_signal['filtered'] = True
                        final_signal['filter_reason'] = filter_reason
                        # 將被過濾的信號轉為HOLD
                        if raw_signal.get('signal') in ['BUY', 'SELL']:
                            final_signal['signal'] = 'HOLD'
                            final_signal['confidence'] *= 0.5  # 降低信心度
                            final_signal['reasons'].append(f"[已過濾] {filter_reason}")
                    
                    all_signals.append(final_signal)
                else:
                    # 數據獲取失敗的fallback信號
                    all_signals.append({
                        'symbol': symbol,
                        'signal': 'HOLD',
                        'confidence': 0.0,
                        'strategy': active_strategy.name,
                        'reasons': ['數據獲取失敗'],
                        'error': True,
                        'filtered': False
                    })
            except Exception as e:
                print(f"Error generating signal for {symbol}: {e}")
                all_signals.append({
                    'symbol': symbol,
                    'signal': 'HOLD',
                    'confidence': 0.0,
                    'strategy': active_strategy.name,
                    'reasons': [f'信號生成錯誤: {str(e)}'],
                    'error': True,
                    'filtered': False
                })
        
        return {
            'signals': all_signals,
            'strategy_used': active_strategy.name,
            'total_signals': len(all_signals),
            'timestamp': pd.Timestamp.now().isoformat()
        }
    
    def generate_signals_multiple_strategies(self, symbol: str) -> Dict:
        """
        使用多個策略為單一股票生成信號
        
        Args:
            symbol (str): 股票代號
            
        Returns:
            Dict: 多策略信號結果
        """
        analyzer = StockAnalyzer(symbol)
        if not analyzer.fetch_data():
            return {'error': f'無法獲取 {symbol} 的數據'}
        
        strategy_signals = self.strategy_manager.generate_signals_all_strategies(symbol, analyzer)
        
        # 計算策略共識
        buy_votes = sum(1 for signal in strategy_signals.values() 
                       if signal.get('signal') == 'BUY')
        sell_votes = sum(1 for signal in strategy_signals.values() 
                        if signal.get('signal') == 'SELL')
        hold_votes = sum(1 for signal in strategy_signals.values() 
                        if signal.get('signal') == 'HOLD')
        
        total_strategies = len(strategy_signals)
        consensus_signal = 'HOLD'
        consensus_confidence = 0.5
        
        if buy_votes > sell_votes and buy_votes > hold_votes:
            consensus_signal = 'BUY'
            consensus_confidence = buy_votes / total_strategies
        elif sell_votes > buy_votes and sell_votes > hold_votes:
            consensus_signal = 'SELL'
            consensus_confidence = sell_votes / total_strategies
        
        return {
            'symbol': symbol,
            'individual_strategies': strategy_signals,
            'consensus': {
                'signal': consensus_signal,
                'confidence': consensus_confidence,
                'buy_votes': buy_votes,
                'sell_votes': sell_votes,
                'hold_votes': hold_votes,
                'total_strategies': total_strategies
            },
            'timestamp': pd.Timestamp.now().isoformat()
        }
    
    def compare_strategy_performance(self, time_horizon: int = 1) -> Dict:
        """
        比較不同策略的預期表現
        
        Args:
            time_horizon (int): 時間範圍（年）
            
        Returns:
            Dict: 策略比較結果
        """
        all_symbols = self.monitored_stocks['US'] + self.monitored_stocks['TW']
        comparison = self.strategy_manager.compare_strategy_returns(all_symbols, time_horizon)
        
        # 添加風險調整後報酬
        for strategy_name in comparison:
            strategy_data = comparison[strategy_name]
            expected_return = strategy_data['expected_annual_return']
            
            # 簡單的風險調整（基於策略風險等級）
            risk_adjustments = {
                'low': 0.8,
                'medium': 1.0,
                'high': 1.3
            }
            
            risk_level = strategy_data.get('risk_level', 'medium')
            risk_adjustment = risk_adjustments.get(risk_level, 1.0)
            
            strategy_data['risk_adjusted_return'] = expected_return / risk_adjustment
            strategy_data['risk_score'] = risk_adjustment
        
        # 排序策略（按風險調整後報酬）
        sorted_strategies = sorted(
            comparison.items(),
            key=lambda x: x[1]['risk_adjusted_return'],
            reverse=True
        )
        
        return {
            'comparison': comparison,
            'ranking': [{'strategy': name, 'data': data} for name, data in sorted_strategies],
            'best_strategy': sorted_strategies[0][0] if sorted_strategies else None,
            'time_horizon': time_horizon
        }
    
    def add_monitored_stock(self, symbol: str, region: str = None) -> bool:
        """
        添加監控股票
        
        Args:
            symbol (str): 股票代號
            region (str): 區域 ('US' 或 'TW')，None則自動判斷
            
        Returns:
            bool: 是否成功添加
        """
        try:
            # 自動判斷區域
            if region is None:
                if '.TW' in symbol:
                    region = 'TW'
                else:
                    region = 'US'
            
            # 確保區域存在
            if region not in self.monitored_stocks:
                self.monitored_stocks[region] = []
            
            # 添加股票（避免重複）
            if symbol not in self.monitored_stocks[region]:
                # 測試股票是否有效
                analyzer = StockAnalyzer(symbol)
                if analyzer.fetch_data():
                    self.monitored_stocks[region].append(symbol)
                    return True
                else:
                    return False
            return True  # 已存在
        except Exception as e:
            print(f"Error adding monitored stock {symbol}: {e}")
            return False
    
    def remove_monitored_stock(self, symbol: str) -> bool:
        """
        移除監控股票
        
        Args:
            symbol (str): 股票代號
            
        Returns:
            bool: 是否成功移除
        """
        try:
            for region in self.monitored_stocks:
                if symbol in self.monitored_stocks[region]:
                    self.monitored_stocks[region].remove(symbol)
                    return True
            return False
        except Exception as e:
            print(f"Error removing monitored stock {symbol}: {e}")
            return False
    
    def get_monitored_stocks(self) -> Dict:
        """
        獲取當前監控的股票列表
        
        Returns:
            Dict: 監控股票字典
        """
        return self.monitored_stocks.copy()
    
    def get_portfolio_strategy_analysis(self, strategy_name: str = None) -> Dict:
        """
        獲取投資組合在特定策略下的分析
        
        Args:
            strategy_name (str): 策略名稱
            
        Returns:
            Dict: 策略投資組合分析
        """
        if strategy_name:
            original_strategy = self.strategy_manager.active_strategy
            self.strategy_manager.set_active_strategy(strategy_name)
        
        try:
            # 獲取投資組合分析
            portfolio_analysis = self.portfolio_manager.get_portfolio_analysis()
            
            # 獲取策略調整倍數
            active_strategy = self.strategy_manager.get_active_strategy()
            strategy_multipliers = {}
            
            if active_strategy:
                # 為投資組合中的每個股票計算策略調整倍數
                for region in self.portfolio_manager.portfolio_data:
                    for symbol in self.portfolio_manager.portfolio_data[region]:
                        try:
                            analyzer = StockAnalyzer(symbol)
                            if analyzer.fetch_data():
                                current_price = analyzer.get_current_price()
                                if current_price:
                                    base_return = active_strategy.calculate_expected_return(symbol, current_price)
                                    strategy_multipliers[symbol] = base_return / 0.08  # 相對於8%基準
                        except:
                            strategy_multipliers[symbol] = 1.0
            
            # 計算策略調整後的預期報酬
            expected_returns = self.portfolio_manager.calculate_expected_returns(
                strategy_multipliers=strategy_multipliers
            )
            
            # 獲取再平衡建議
            rebalance_suggestions = self.portfolio_manager.get_rebalance_suggestions(
                strategy_name=active_strategy.name if active_strategy else None
            )
            
            return {
                'portfolio_analysis': portfolio_analysis,
                'expected_returns': expected_returns,
                'rebalance_suggestions': rebalance_suggestions,
                'strategy_used': active_strategy.name if active_strategy else 'none',
                'strategy_multipliers': strategy_multipliers
            }
            
        finally:
            # 恢復原策略
            if strategy_name and original_strategy:
                self.strategy_manager.set_active_strategy(original_strategy)

import pandas as pd