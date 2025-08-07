"""
投資組合管理器模組
提供投資組合分析、再平衡和預期報酬計算功能
"""

import math
from typing import Dict, List, Optional, Tuple
from modules.stock_analyzer import StockAnalyzer
from utils.constants import (
    DEFAULT_USER_PORTFOLIO, DEFAULT_PORTFOLIO_CONFIG, 
    EXPECTED_RETURNS, VOLATILITY, REBALANCE_CONFIG
)

class PortfolioManager:
    """投資組合管理器"""
    
    def __init__(self, portfolio_data: Dict = None, target_config: Dict = None):
        """
        初始化投資組合管理器
        
        Args:
            portfolio_data (Dict): 用戶投資組合數據
            target_config (Dict): 目標配置
        """
        self.portfolio_data = portfolio_data or DEFAULT_USER_PORTFOLIO.copy()
        self.target_config = target_config or DEFAULT_PORTFOLIO_CONFIG.copy()
        
        # 添加當前市值字段
        for region in self.portfolio_data:
            for symbol in self.portfolio_data[region]:
                if 'current_value' not in self.portfolio_data[region][symbol]:
                    self.portfolio_data[region][symbol]['current_value'] = 0
                if 'current_price' not in self.portfolio_data[region][symbol]:
                    self.portfolio_data[region][symbol]['current_price'] = 0
    
    def update_current_values(self) -> bool:
        """
        更新當前市值
        
        Returns:
            bool: 是否成功更新
        """
        try:
            all_symbols = []
            
            # 收集所有股票代號
            for region in self.portfolio_data:
                all_symbols.extend(list(self.portfolio_data[region].keys()))
            
            # 批量更新價格
            for symbol in all_symbols:
                analyzer = StockAnalyzer(symbol)
                if analyzer.fetch_data():
                    current_price = analyzer.get_current_price()
                    if current_price:
                        # 找到並更新對應的持股
                        for region in self.portfolio_data:
                            if symbol in self.portfolio_data[region]:
                                shares = self.portfolio_data[region][symbol]['shares']
                                self.portfolio_data[region][symbol]['current_value'] = shares * current_price
                                self.portfolio_data[region][symbol]['current_price'] = current_price
                                break
            
            return True
        except Exception as e:
            print(f"Error updating portfolio values: {e}")
            return False
    
    def get_portfolio_analysis(self) -> Dict:
        """
        獲取投資組合分析
        
        Returns:
            Dict: 投資組合分析結果
        """
        self.update_current_values()
        
        # 計算各區域總值
        region_totals = {}
        for region in self.portfolio_data:
            region_totals[region] = sum([
                stock['current_value'] 
                for stock in self.portfolio_data[region].values()
            ])
        
        total_value = sum(region_totals.values())
        
        # 計算當前權重和目標權重
        current_weights = {}
        target_weights = {}
        rebalance_needed = {}
        
        for region in self.portfolio_data:
            region_total = region_totals[region]
            
            for symbol, data in self.portfolio_data[region].items():
                if region_total > 0:
                    current_weight = data['current_value'] / region_total
                else:
                    current_weight = 0
                
                target_weight = self.target_config.get(region, {}).get(symbol, {}).get('target_weight', 0)
                
                current_weights[symbol] = current_weight
                target_weights[symbol] = target_weight
                
                # 判斷是否需要再平衡
                weight_diff = abs(current_weight - target_weight)
                rebalance_needed[symbol] = weight_diff > REBALANCE_CONFIG['ALERT_THRESHOLD']
        
        # 計算損益
        total_cost = 0
        total_gain_loss = 0
        
        for region in self.portfolio_data:
            for symbol, data in self.portfolio_data[region].items():
                cost = data['shares'] * data['avg_cost']
                current_value = data['current_value']
                total_cost += cost
                total_gain_loss += (current_value - cost)
        
        return {
            'total_value': {
                'us_stocks': region_totals.get('US_STOCKS', 0),
                'tw_stocks': region_totals.get('TW_STOCKS', 0),
                'total': total_value
            },
            'current_weights': current_weights,
            'target_weights': target_weights,
            'rebalance_needed': rebalance_needed,
            'performance': {
                'total_cost': total_cost,
                'total_value': total_value,
                'total_gain_loss': total_gain_loss,
                'total_return_pct': (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
            },
            'holdings_detail': self._get_holdings_detail()
        }
    
    def get_rebalance_suggestions(self, strategy_name: str = None) -> List[Dict]:
        """
        獲取再平衡建議
        
        Args:
            strategy_name (str): 策略名稱，不同策略有不同的再平衡邏輯
            
        Returns:
            List[Dict]: 再平衡建議列表
        """
        analysis = self.get_portfolio_analysis()
        suggestions = []
        
        # 美股再平衡建議
        us_total = analysis['total_value']['us_stocks']
        if us_total > 0:
            suggestions.extend(self._generate_region_rebalance_suggestions(
                'US_STOCKS', us_total, analysis, strategy_name
            ))
        
        # 台股再平衡建議
        tw_total = analysis['total_value']['tw_stocks']
        if tw_total > 0:
            suggestions.extend(self._generate_region_rebalance_suggestions(
                'TW_STOCKS', tw_total, analysis, strategy_name
            ))
        
        return suggestions
    
    def calculate_expected_returns(self, strategy_multipliers: Dict = None, time_horizon: int = 1) -> Dict:
        """
        計算預期報酬率
        
        Args:
            strategy_multipliers (Dict): 策略調整倍數
            time_horizon (int): 時間範圍（年）
            
        Returns:
            Dict: 預期報酬分析
        """
        analysis = self.get_portfolio_analysis()
        total_value = analysis['total_value']['total']
        
        if total_value == 0:
            return self._empty_return_analysis()
        
        expected_return = 0
        risk = 0
        
        # 計算加權平均預期報酬率和風險
        for region in self.portfolio_data:
            for symbol, data in self.portfolio_data[region].items():
                weight = data['current_value'] / total_value
                base_return = EXPECTED_RETURNS.get(symbol, 0.08)
                
                # 應用策略調整倍數
                if strategy_multipliers and symbol in strategy_multipliers:
                    adjusted_return = base_return * strategy_multipliers[symbol]
                else:
                    adjusted_return = base_return
                
                expected_return += weight * adjusted_return
                
                # 計算風險（方差）
                volatility = VOLATILITY.get(symbol, 0.15)
                risk += weight * weight * (volatility ** 2)
        
        portfolio_volatility = math.sqrt(risk)
        
        # 計算不同時間範圍的預期值
        return {
            'current_value': total_value,
            'expected_annual_return': expected_return,
            'expected_volatility': portfolio_volatility,
            'sharpe_ratio': expected_return / portfolio_volatility if portfolio_volatility > 0 else 0,
            'projected_value_1y': total_value * (1 + expected_return),
            'projected_value_3y': total_value * ((1 + expected_return) ** 3),
            'projected_value_5y': total_value * ((1 + expected_return) ** 5),
            'projected_value_10y': total_value * ((1 + expected_return) ** 10),
            'best_case_1y': total_value * (1 + expected_return + portfolio_volatility),
            'worst_case_1y': total_value * (1 + expected_return - portfolio_volatility),
            'var_95_1y': total_value * (1 + expected_return - 1.645 * portfolio_volatility),  # 95% VaR
        }
    
    def add_stock_to_portfolio(self, symbol: str, shares: float, avg_cost: float, region: str = None) -> bool:
        """
        添加股票到投資組合
        
        Args:
            symbol (str): 股票代號
            shares (float): 股數
            avg_cost (float): 平均成本
            region (str): 區域 ('US_STOCKS' 或 'TW_STOCKS')
            
        Returns:
            bool: 是否成功添加
        """
        try:
            # 自動判斷區域
            if region is None:
                if '.TW' in symbol:
                    region = 'TW_STOCKS'
                else:
                    region = 'US_STOCKS'
            
            # 確保區域存在
            if region not in self.portfolio_data:
                self.portfolio_data[region] = {}
            
            # 添加或更新持股
            if symbol in self.portfolio_data[region]:
                # 更新現有持股
                existing = self.portfolio_data[region][symbol]
                total_shares = existing['shares'] + shares
                total_cost = existing['shares'] * existing['avg_cost'] + shares * avg_cost
                new_avg_cost = total_cost / total_shares
                
                self.portfolio_data[region][symbol].update({
                    'shares': total_shares,
                    'avg_cost': new_avg_cost
                })
            else:
                # 新增持股
                self.portfolio_data[region][symbol] = {
                    'shares': shares,
                    'avg_cost': avg_cost,
                    'current_value': 0,
                    'current_price': 0
                }
            
            return True
        except Exception as e:
            print(f"Error adding stock to portfolio: {e}")
            return False
    
    def remove_stock_from_portfolio(self, symbol: str) -> bool:
        """
        從投資組合中移除股票
        
        Args:
            symbol (str): 股票代號
            
        Returns:
            bool: 是否成功移除
        """
        try:
            for region in self.portfolio_data:
                if symbol in self.portfolio_data[region]:
                    del self.portfolio_data[region][symbol]
                    return True
            return False
        except Exception as e:
            print(f"Error removing stock from portfolio: {e}")
            return False
    
    def _generate_region_rebalance_suggestions(self, region: str, region_total: float, 
                                             analysis: Dict, strategy_name: str = None) -> List[Dict]:
        """
        生成特定區域的再平衡建議
        
        Args:
            region (str): 區域名稱
            region_total (float): 區域總值
            analysis (Dict): 投資組合分析結果
            strategy_name (str): 策略名稱
            
        Returns:
            List[Dict]: 再平衡建議
        """
        suggestions = []
        threshold = REBALANCE_CONFIG['THRESHOLD']
        min_amount = REBALANCE_CONFIG['MIN_AMOUNT']
        
        for symbol in self.portfolio_data[region]:
            current_weight = analysis['current_weights'].get(symbol, 0)
            target_weight = analysis['target_weights'].get(symbol, 0)
            weight_diff = current_weight - target_weight
            
            if abs(weight_diff) > threshold:
                amount_diff = region_total * weight_diff
                
                if abs(amount_diff) > min_amount:
                    action = 'SELL' if amount_diff > 0 else 'BUY'
                    suggestions.append({
                        'action': action,
                        'symbol': symbol,
                        'amount': abs(amount_diff),
                        'reason': f'{symbol}{"超出" if action == "SELL" else "低於"}目標配置{target_weight:.1%}，當前{current_weight:.1%}',
                        'current_weight': current_weight,
                        'target_weight': target_weight,
                        'strategy': strategy_name or 'default'
                    })
        
        return suggestions
    
    def _get_holdings_detail(self) -> Dict:
        """
        獲取持股詳細信息
        
        Returns:
            Dict: 持股詳細信息
        """
        detail = {}
        
        for region in self.portfolio_data:
            detail[region] = {}
            for symbol, data in self.portfolio_data[region].items():
                cost = data['shares'] * data['avg_cost']
                current_value = data['current_value']
                gain_loss = current_value - cost
                gain_loss_pct = (gain_loss / cost * 100) if cost > 0 else 0
                
                detail[region][symbol] = {
                    'shares': data['shares'],
                    'avg_cost': data['avg_cost'],
                    'current_price': data['current_price'],
                    'total_cost': cost,
                    'current_value': current_value,
                    'gain_loss': gain_loss,
                    'gain_loss_pct': gain_loss_pct
                }
        
        return detail
    
    def _empty_return_analysis(self) -> Dict:
        """
        返回空的報酬分析
        
        Returns:
            Dict: 空的報酬分析
        """
        return {
            'current_value': 0,
            'expected_annual_return': 0,
            'expected_volatility': 0,
            'sharpe_ratio': 0,
            'projected_value_1y': 0,
            'projected_value_3y': 0,
            'projected_value_5y': 0,
            'projected_value_10y': 0,
            'best_case_1y': 0,
            'worst_case_1y': 0,
            'var_95_1y': 0
        }