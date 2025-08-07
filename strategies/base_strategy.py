"""
基礎策略類
所有交易策略的基類
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
from modules.stock_analyzer import StockAnalyzer

class BaseStrategy(ABC):
    """基礎策略抽象類"""
    
    def __init__(self, name: str, description: str):
        """
        初始化策略
        
        Args:
            name (str): 策略名稱
            description (str): 策略描述
        """
        self.name = name
        self.description = description
        
    @abstractmethod
    def generate_signal(self, analyzer: StockAnalyzer, **kwargs) -> Dict:
        """
        生成交易信號
        
        Args:
            analyzer (StockAnalyzer): 股票分析器
            **kwargs: 額外參數
            
        Returns:
            Dict: 交易信號字典
        """
        pass
    
    @abstractmethod
    def calculate_expected_return(self, symbol: str, current_price: float) -> float:
        """
        計算預期報酬率
        
        Args:
            symbol (str): 股票代號
            current_price (float): 當前價格
            
        Returns:
            float: 預期年化報酬率
        """
        pass
    
    def format_signal(self, symbol: str, signal: str, confidence: float, 
                     reasons: List[str], additional_data: Dict = None, 
                     risk_management: Dict = None) -> Dict:
        """
        格式化交易信號
        
        Args:
            symbol (str): 股票代號
            signal (str): 信號類型 ('BUY', 'SELL', 'HOLD')
            confidence (float): 信心度 (0-1)
            reasons (List[str]): 信號原因
            additional_data (Dict): 額外數據
            risk_management (Dict): 風險管理信息
            
        Returns:
            Dict: 格式化的信號
        """
        result = {
            'symbol': symbol,
            'signal': signal,
            'confidence': confidence,
            'strategy': self.name,
            'reasons': reasons,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        if additional_data:
            result.update(additional_data)
        
        if risk_management:
            result['risk_management'] = risk_management
            
        return result

class StrategyManager:
    """策略管理器"""
    
    def __init__(self):
        """初始化策略管理器"""
        self.strategies: Dict[str, BaseStrategy] = {}
        self.active_strategy: Optional[str] = None
        
    def register_strategy(self, strategy: BaseStrategy) -> None:
        """
        註冊策略
        
        Args:
            strategy (BaseStrategy): 策略實例
        """
        self.strategies[strategy.name] = strategy
        
        # 如果是第一個策略，設為活躍策略
        if self.active_strategy is None:
            self.active_strategy = strategy.name
    
    def set_active_strategy(self, strategy_name: str) -> bool:
        """
        設置活躍策略
        
        Args:
            strategy_name (str): 策略名稱
            
        Returns:
            bool: 是否成功設置
        """
        if strategy_name in self.strategies:
            self.active_strategy = strategy_name
            return True
        return False
    
    def get_active_strategy(self) -> Optional[BaseStrategy]:
        """
        獲取當前活躍策略
        
        Returns:
            BaseStrategy: 當前活躍策略
        """
        if self.active_strategy:
            return self.strategies.get(self.active_strategy)
        return None
    
    def get_all_strategies(self) -> Dict[str, BaseStrategy]:
        """
        獲取所有策略
        
        Returns:
            Dict[str, BaseStrategy]: 所有策略字典
        """
        return self.strategies.copy()
    
    def generate_signals_all_strategies(self, symbol: str, analyzer: StockAnalyzer) -> Dict[str, Dict]:
        """
        使用所有策略生成信號
        
        Args:
            symbol (str): 股票代號
            analyzer (StockAnalyzer): 股票分析器
            
        Returns:
            Dict[str, Dict]: 所有策略的信號
        """
        signals = {}
        
        for strategy_name, strategy in self.strategies.items():
            try:
                signal = strategy.generate_signal(analyzer, symbol=symbol)
                signals[strategy_name] = signal
            except Exception as e:
                print(f"Error generating signal for {strategy_name} on {symbol}: {e}")
                signals[strategy_name] = {
                    'error': str(e),
                    'signal': 'HOLD',
                    'confidence': 0.0
                }
                
        return signals
    
    def compare_strategy_returns(self, symbols: List[str], time_horizon: int = 1) -> Dict:
        """
        比較不同策略的預期報酬
        
        Args:
            symbols (List[str]): 股票代號列表
            time_horizon (int): 時間範圍（年）
            
        Returns:
            Dict: 策略比較結果
        """
        comparison = {}
        
        # 獲取當前價格
        current_prices = {}
        for symbol in symbols:
            analyzer = StockAnalyzer(symbol)
            if analyzer.fetch_data():
                current_prices[symbol] = analyzer.get_current_price()
        
        # 計算每個策略的預期報酬
        for strategy_name, strategy in self.strategies.items():
            total_return = 0
            valid_symbols = 0
            
            for symbol in symbols:
                if symbol in current_prices and current_prices[symbol]:
                    try:
                        expected_return = strategy.calculate_expected_return(
                            symbol, current_prices[symbol]
                        )
                        total_return += expected_return
                        valid_symbols += 1
                    except Exception as e:
                        print(f"Error calculating return for {strategy_name} on {symbol}: {e}")
            
            if valid_symbols > 0:
                avg_return = total_return / valid_symbols
                comparison[strategy_name] = {
                    'expected_annual_return': avg_return,
                    'expected_total_return': avg_return * time_horizon,
                    'risk_level': getattr(strategy, 'risk_level', 'medium'),
                    'valid_symbols': valid_symbols
                }
        
        return comparison