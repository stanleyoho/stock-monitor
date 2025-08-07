from flask import Flask, render_template, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import math
from config import *

app = Flask(__name__)

class StockAnalyzer:
    def __init__(self, symbol):
        self.symbol = symbol
        self.data = None
        
    def fetch_data(self, period='3mo'):
        """獲取股票數據"""
        try:
            ticker = yf.Ticker(self.symbol)
            self.data = ticker.history(period=period)
            return True
        except Exception as e:
            print(f"Error fetching data for {self.symbol}: {e}")
            return False
    
    def calculate_sma(self, window=20):
        """計算簡單移動平均線"""
        if self.data is not None:
            return self.data['Close'].rolling(window=window).mean()
        return None
    
    def calculate_rsi(self, window=14):
        """計算RSI指標"""
        if self.data is None:
            return None
            
        close_prices = self.data['Close']
        delta = close_prices.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self):
        """計算MACD指標"""
        if self.data is None:
            return None, None, None
            
        close_prices = self.data['Close']
        exp1 = close_prices.ewm(span=MACD_FAST).mean()
        exp2 = close_prices.ewm(span=MACD_SLOW).mean()
        
        macd = exp1 - exp2
        signal = macd.ewm(span=MACD_SIGNAL).mean()
        histogram = macd - signal
        
        return macd, signal, histogram
    
    def get_vix_data(self):
        """獲取VIX恐慌指數"""
        try:
            vix_ticker = yf.Ticker("^VIX")
            vix_data = vix_ticker.history(period="5d")
            if not vix_data.empty:
                return float(vix_data['Close'].iloc[-1])
        except:
            pass
        return None
    
    def get_trading_signal(self):
        """根據策略1生成買賣信號"""
        if self.data is None:
            return None
            
        current_price = float(self.data['Close'].iloc[-1])
        sma_20 = self.calculate_sma(20)
        rsi = self.calculate_rsi()
        
        if sma_20 is None or rsi is None:
            return None
            
        current_sma = float(sma_20.iloc[-1])
        current_rsi = float(rsi.iloc[-1])
        
        # 策略1邏輯
        signal = {
            'symbol': self.symbol,
            'current_price': current_price,
            'sma_20': current_sma,
            'rsi': current_rsi,
            'signal': 'HOLD',
            'reason': '',
            'timestamp': datetime.now().isoformat()
        }
        
        # 買入信號：股價跌破20日均線且RSI<30
        if current_price < current_sma and current_rsi < 30:
            signal['signal'] = 'BUY'
            signal['reason'] = f'價格({current_price:.2f}) < SMA20({current_sma:.2f}) 且 RSI({current_rsi:.1f}) < 30'
        
        # 賣出信號：股價突破20日均線且RSI>70  
        elif current_price > current_sma and current_rsi > 70:
            signal['signal'] = 'SELL'
            signal['reason'] = f'價格({current_price:.2f}) > SMA20({current_sma:.2f}) 且 RSI({current_rsi:.1f}) > 70'
        
        else:
            signal['reason'] = f'價格:{current_price:.2f}, SMA20:{current_sma:.2f}, RSI:{current_rsi:.1f} - 無明確信號'
            
        return signal

class PortfolioManager:
    def __init__(self):
        self.current_portfolio = {
            'US_STOCKS': {
                'VOO': {'shares': 94, 'avg_cost': 555.38, 'current_value': 0},
                'NVDA': {'shares': 167, 'avg_cost': 163.98, 'current_value': 0},
                'QQQ': {'shares': 25, 'avg_cost': 532.57, 'current_value': 0}
            },
            'TW_STOCKS': {
                '00878.TW': {'shares': 36300, 'avg_cost': 20.83, 'current_value': 0},
                '0050.TW': {'shares': 4900, 'avg_cost': 47.92, 'current_value': 0}
            }
        }
    
    def update_current_values(self):
        """更新當前市值"""
        all_symbols = list(self.current_portfolio['US_STOCKS'].keys()) + list(self.current_portfolio['TW_STOCKS'].keys())
        
        for symbol in all_symbols:
            analyzer = StockAnalyzer(symbol)
            if analyzer.fetch_data():
                current_price = float(analyzer.data['Close'].iloc[-1])
                
                if symbol in self.current_portfolio['US_STOCKS']:
                    shares = self.current_portfolio['US_STOCKS'][symbol]['shares']
                    self.current_portfolio['US_STOCKS'][symbol]['current_value'] = shares * current_price
                    self.current_portfolio['US_STOCKS'][symbol]['current_price'] = current_price
                elif symbol in self.current_portfolio['TW_STOCKS']:
                    shares = self.current_portfolio['TW_STOCKS'][symbol]['shares']
                    self.current_portfolio['TW_STOCKS'][symbol]['current_value'] = shares * current_price
                    self.current_portfolio['TW_STOCKS'][symbol]['current_price'] = current_price
    
    def get_portfolio_analysis(self):
        """獲取投資組合分析"""
        self.update_current_values()
        
        # 計算總值
        us_total = sum([stock['current_value'] for stock in self.current_portfolio['US_STOCKS'].values()])
        tw_total = sum([stock['current_value'] for stock in self.current_portfolio['TW_STOCKS'].values()])
        
        # 計算實際權重
        analysis = {
            'total_value': {
                'us_stocks': us_total,
                'tw_stocks': tw_total,
                'total': us_total + tw_total
            },
            'current_weights': {},
            'target_weights': {},
            'rebalance_needed': {},
            'trade_suggestions': []
        }
        
        # 計算美股權重
        for symbol, data in self.current_portfolio['US_STOCKS'].items():
            current_weight = data['current_value'] / us_total if us_total > 0 else 0
            target_weight = PORTFOLIO_CONFIG['US_STOCKS'][symbol]['target_weight']
            
            analysis['current_weights'][symbol] = current_weight
            analysis['target_weights'][symbol] = target_weight
            analysis['rebalance_needed'][symbol] = abs(current_weight - target_weight) > REBALANCE_ALERT_THRESHOLD
        
        # 計算台股權重
        for symbol, data in self.current_portfolio['TW_STOCKS'].items():
            current_weight = data['current_value'] / tw_total if tw_total > 0 else 0
            target_weight = PORTFOLIO_CONFIG['TW_STOCKS'][symbol]['target_weight']
            
            analysis['current_weights'][symbol] = current_weight
            analysis['target_weights'][symbol] = target_weight
            analysis['rebalance_needed'][symbol] = abs(current_weight - target_weight) > REBALANCE_ALERT_THRESHOLD
        
        return analysis
    
    def get_rebalance_suggestions(self):
        """獲取再平衡建議"""
        analysis = self.get_portfolio_analysis()
        suggestions = []
        
        # 美股再平衡建議
        us_total = analysis['total_value']['us_stocks']
        for symbol in self.current_portfolio['US_STOCKS'].keys():
            current_weight = analysis['current_weights'][symbol]
            target_weight = analysis['target_weights'][symbol]
            weight_diff = current_weight - target_weight
            
            if abs(weight_diff) > REBALANCE_THRESHOLD:
                target_value = us_total * target_weight
                current_value = us_total * current_weight
                amount_diff = target_value - current_value
                
                if amount_diff > 0:
                    suggestions.append({
                        'action': 'BUY',
                        'symbol': symbol,
                        'amount': amount_diff,
                        'reason': f'{symbol}低於目標配置{target_weight:.1%}，當前{current_weight:.1%}'
                    })
                else:
                    suggestions.append({
                        'action': 'SELL',
                        'symbol': symbol,
                        'amount': abs(amount_diff),
                        'reason': f'{symbol}超出目標配置{target_weight:.1%}，當前{current_weight:.1%}'
                    })
        
        # 台股再平衡建議
        tw_total = analysis['total_value']['tw_stocks']
        for symbol in self.current_portfolio['TW_STOCKS'].keys():
            current_weight = analysis['current_weights'][symbol]
            target_weight = analysis['target_weights'][symbol]
            weight_diff = current_weight - target_weight
            
            if abs(weight_diff) > REBALANCE_THRESHOLD:
                target_value = tw_total * target_weight
                current_value = tw_total * current_weight
                amount_diff = target_value - current_value
                
                if amount_diff > 0:
                    suggestions.append({
                        'action': 'BUY',
                        'symbol': symbol,
                        'amount': amount_diff,
                        'reason': f'{symbol}低於目標配置{target_weight:.1%}，當前{current_weight:.1%}'
                    })
                else:
                    suggestions.append({
                        'action': 'SELL',
                        'symbol': symbol,
                        'amount': abs(amount_diff),
                        'reason': f'{symbol}超出目標配置{target_weight:.1%}，當前{current_weight:.1%}'
                    })
        
        return suggestions
    
    def calculate_expected_returns(self, time_horizon=1):
        """計算預期報酬率"""
        analysis = self.get_portfolio_analysis()
        total_value = analysis['total_value']['total']
        
        expected_return = 0
        risk = 0
        
        # 美股部分
        for symbol, data in self.current_portfolio['US_STOCKS'].items():
            weight = data['current_value'] / total_value if total_value > 0 else 0
            expected_return += weight * EXPECTED_RETURNS.get(symbol, 0.08)
            risk += weight * weight * (VOLATILITY.get(symbol, 0.15) ** 2)
        
        # 台股部分
        for symbol, data in self.current_portfolio['TW_STOCKS'].items():
            weight = data['current_value'] / total_value if total_value > 0 else 0
            expected_return += weight * EXPECTED_RETURNS.get(symbol, 0.06)
            risk += weight * weight * (VOLATILITY.get(symbol, 0.12) ** 2)
        
        portfolio_volatility = math.sqrt(risk)
        
        # 考慮時間範圍
        projected_return = expected_return * time_horizon
        projected_value = total_value * (1 + projected_return)
        
        return {
            'current_value': total_value,
            'expected_annual_return': expected_return,
            'expected_volatility': portfolio_volatility,
            'projected_value_1y': total_value * (1 + expected_return),
            'projected_value_3y': total_value * ((1 + expected_return) ** 3),
            'projected_value_5y': total_value * ((1 + expected_return) ** 5),
            'best_case_1y': total_value * (1 + expected_return + portfolio_volatility),
            'worst_case_1y': total_value * (1 + expected_return - portfolio_volatility)
        }

class StrategySignalGenerator:
    def __init__(self):
        self.portfolio_manager = PortfolioManager()
    
    def get_enhanced_signals(self):
        """獲取增強版交易信號"""
        signals = []
        vix_level = None
        
        # 獲取VIX數據
        try:
            vix_analyzer = StockAnalyzer("^VIX")
            if vix_analyzer.fetch_data():
                vix_level = float(vix_analyzer.data['Close'].iloc[-1])
        except:
            pass
        
        # 為每個股票生成信號
        all_symbols = STOCKS + TW_STOCKS
        for symbol in all_symbols:
            analyzer = StockAnalyzer(symbol)
            if analyzer.fetch_data():
                signal = self.generate_strategy_signal(analyzer, symbol, vix_level)
                signals.append(signal)
        
        return {
            'signals': signals,
            'vix_level': vix_level,
            'market_sentiment': self.get_market_sentiment(vix_level),
            'portfolio_suggestions': self.portfolio_manager.get_rebalance_suggestions()
        }
    
    def generate_strategy_signal(self, analyzer, symbol, vix_level):
        """為特定股票生成策略信號"""
        current_price = float(analyzer.data['Close'].iloc[-1])
        sma_20 = analyzer.calculate_sma(20)
        sma_50 = analyzer.calculate_sma(50)
        rsi = analyzer.calculate_rsi()
        macd, macd_signal, macd_histogram = analyzer.calculate_macd()
        
        signal = {
            'symbol': symbol,
            'current_price': current_price,
            'sma_20': float(sma_20.iloc[-1]) if sma_20 is not None else None,
            'sma_50': float(sma_50.iloc[-1]) if sma_50 is not None else None,
            'rsi': float(rsi.iloc[-1]) if rsi is not None else None,
            'macd': float(macd.iloc[-1]) if macd is not None else None,
            'macd_signal': float(macd_signal.iloc[-1]) if macd_signal is not None else None,
            'signal': 'HOLD',
            'strategy': 'mixed',
            'confidence': 0.5,
            'reasons': [],
            'stop_loss_price': None,
            'target_price': None
        }
        
        # 應用不同策略邏輯
        if symbol == 'NVDA':
            self.apply_nvda_strategy(signal, analyzer, vix_level)
        elif symbol == 'QQQ':
            self.apply_qqq_strategy(signal, analyzer, vix_level)
        elif symbol == 'VOO':
            self.apply_voo_strategy(signal, analyzer, vix_level)
        elif symbol in TW_STOCKS:
            self.apply_tw_strategy(signal, analyzer)
        
        return signal
    
    def apply_nvda_strategy(self, signal, analyzer, vix_level):
        """NVDA動量策略"""
        price = signal['current_price']
        sma_20 = signal['sma_20']
        rsi = signal['rsi']
        
        confidence = 0.5
        reasons = []
        
        # 加碼條件
        if price > sma_20 and 30 < rsi < 70:
            signal['signal'] = 'BUY'
            reasons.append('價格突破20日均線且RSI在健康區間')
            confidence += 0.3
            signal['target_price'] = price * 1.15
        
        # 減碼條件
        elif price < sma_20 and rsi < 50:
            signal['signal'] = 'SELL'
            reasons.append('跌破20日均線且RSI轉弱')
            confidence += 0.2
        
        # VIX調整
        if vix_level and vix_level > VIX_PANIC_LEVEL:
            if signal['signal'] == 'BUY':
                signal['signal'] = 'HOLD'
                reasons.append('VIX高位，暫緩買入')
            elif signal['signal'] == 'SELL':
                confidence += 0.2
                reasons.append('VIX高位，建議減持')
        
        signal['stop_loss_price'] = price * (1 - STOP_LOSS.get('NVDA', 0.15))
        signal['confidence'] = min(confidence, 1.0)
        signal['reasons'] = reasons
        signal['strategy'] = 'momentum'
    
    def apply_qqq_strategy(self, signal, analyzer, vix_level):
        """QQQ趨勢策略"""
        price = signal['current_price']
        sma_20 = signal['sma_20']
        sma_50 = signal['sma_50']
        macd = signal['macd']
        macd_signal_line = signal['macd_signal']
        
        confidence = 0.5
        reasons = []
        
        # 趨勢確認
        if sma_20 and sma_50 and sma_20 > sma_50:
            if price > sma_20 and macd and macd_signal_line and macd > macd_signal_line:
                signal['signal'] = 'BUY'
                reasons.append('多重趨勢確認向上')
                confidence += 0.3
        elif sma_20 and sma_50 and sma_20 < sma_50:
            if price < sma_50:
                signal['signal'] = 'SELL'
                reasons.append('趨勢轉弱，跌破關鍵均線')
                confidence += 0.2
        
        signal['stop_loss_price'] = price * (1 - STOP_LOSS.get('QQQ', 0.12))
        signal['confidence'] = min(confidence, 1.0)
        signal['reasons'] = reasons
        signal['strategy'] = 'trend'
    
    def apply_voo_strategy(self, signal, analyzer, vix_level):
        """VOO穩健策略"""
        price = signal['current_price']
        sma_20 = signal['sma_20']
        
        confidence = 0.3
        reasons = []
        
        # 定期定額邏輯
        signal['signal'] = 'BUY'
        reasons.append('定期定額，長期投資')
        
        # VIX調整
        if vix_level:
            if vix_level > 25:
                confidence += 0.4
                reasons.append(f'VIX={vix_level:.1f}，恐慌時機加碼')
            elif vix_level < 15:
                confidence -= 0.2
                reasons.append('市場過熱，保持謹慎')
        
        signal['confidence'] = max(confidence, 0.1)
        signal['reasons'] = reasons
        signal['strategy'] = 'steady'
    
    def apply_tw_strategy(self, signal, analyzer):
        """台股策略"""
        price = signal['current_price']
        sma_20 = signal['sma_20']
        
        confidence = 0.4
        reasons = []
        
        if signal['symbol'] == '00878.TW':
            # 高股息策略
            signal['signal'] = 'HOLD'
            reasons.append('高股息ETF，持續持有領息')
        elif signal['symbol'] == '0050.TW':
            # 台股大盤策略
            if sma_20 and price < sma_20 * 0.95:
                signal['signal'] = 'BUY'
                reasons.append('台股回檔，逢低承接')
                confidence += 0.3
        
        signal['confidence'] = confidence
        signal['reasons'] = reasons
        signal['strategy'] = 'taiwan'
    
    def get_market_sentiment(self, vix_level):
        """獲取市場情緒"""
        if not vix_level:
            return 'unknown'
        
        if vix_level > 30:
            return 'panic'
        elif vix_level > 20:
            return 'fear'
        elif vix_level > 15:
            return 'neutral'
        else:
            return 'greed'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/signals')
def get_signals():
    """API端點：獲取所有股票的買賣信號"""
    try:
        strategy_generator = StrategySignalGenerator()
        enhanced_signals = strategy_generator.get_enhanced_signals()
        
        return jsonify({
            'success': True,
            'data': enhanced_signals['signals'],
            'vix_level': enhanced_signals['vix_level'],
            'market_sentiment': enhanced_signals['market_sentiment'],
            'portfolio_suggestions': enhanced_signals['portfolio_suggestions'],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/portfolio')
def get_portfolio():
    """API端點：獲取投資組合分析"""
    try:
        portfolio_manager = PortfolioManager()
        analysis = portfolio_manager.get_portfolio_analysis()
        expected_returns = portfolio_manager.calculate_expected_returns()
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'expected_returns': expected_returns,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/rebalance')
def get_rebalance_suggestions():
    """API端點：獲取再平衡建議"""
    try:
        portfolio_manager = PortfolioManager()
        suggestions = portfolio_manager.get_rebalance_suggestions()
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/stock/<symbol>')
def get_stock_detail(symbol):
    """API端點：獲取特定股票詳細信息"""
    analyzer = StockAnalyzer(symbol.upper())
    
    if not analyzer.fetch_data():
        return jsonify({
            'success': False,
            'error': f'Failed to fetch data for {symbol}'
        })
    
    # 獲取歷史數據
    sma_20 = analyzer.calculate_sma(20)
    rsi = analyzer.calculate_rsi()
    signal = analyzer.get_trading_signal()
    
    # 準備圖表數據
    chart_data = {
        'dates': analyzer.data.index.strftime('%Y-%m-%d').tolist(),
        'prices': analyzer.data['Close'].tolist(),
        'sma_20': sma_20.tolist(),
        'rsi': rsi.tolist(),
        'volume': analyzer.data['Volume'].tolist()
    }
    
    return jsonify({
        'success': True,
        'symbol': symbol.upper(),
        'signal': signal,
        'chart_data': chart_data
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)