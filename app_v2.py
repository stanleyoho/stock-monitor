"""
股票監控系統主應用 (版本2)
使用模組化架構和多策略系統
"""

from flask import Flask, render_template, jsonify, request
import pandas as pd
from datetime import datetime
import sys
import os

# 添加模組路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.multi_strategy_engine import MultiStrategyEngine
from modules.stock_analyzer import StockAnalyzer, VIXAnalyzer
from modules.risk_manager import RiskManager
from utils.constants import FLASK_CONFIG, STOCK_NAMES, MARKET_SENTIMENT
from utils.error_handler import (
    error_handler, handle_api_exceptions, StockMonitorError, 
    DataFetchError, APIError, ValidationError
)

app = Flask(__name__)

# 全局多策略引擎實例
strategy_engine = MultiStrategyEngine()
risk_manager = RiskManager()

@app.route('/')
def index():
    """主頁面"""
    return render_template('index_ultra_compact.html')

@app.route('/api/strategies')
def get_strategies():
    """API端點：獲取所有可用策略"""
    try:
        strategies = strategy_engine.get_available_strategies()
        return jsonify({
            'success': True,
            'strategies': strategies,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/strategy/switch', methods=['POST'])
def switch_strategy():
    """API端點：切換活躍策略"""
    try:
        data = request.get_json()
        strategy_name = data.get('strategy_name')
        
        if not strategy_name:
            return jsonify({
                'success': False,
                'error': '缺少策略名稱參數'
            }), 400
        
        success = strategy_engine.switch_strategy(strategy_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'成功切換到{strategy_name}策略',
                'active_strategy': strategy_name,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': f'策略{strategy_name}不存在',
                'timestamp': datetime.now().isoformat()
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/signals')
@handle_api_exceptions
def get_signals():
    """API端點：獲取所有股票的交易信號"""
    # 獲取查詢參數
    strategy_name = request.args.get('strategy')
    
    # 生成信號
    signals_data = strategy_engine.generate_signals_all_stocks(strategy_name)
    
    if not signals_data or 'signals' not in signals_data:
        raise APIError('/api/signals', '信號生成失敗')
    
    if 'error' in signals_data:
        raise APIError('/api/signals', signals_data['error'])
    
    # 獲取VIX和市場情緒 - 非關鍵數據，錯誤時繼續
    try:
        vix_level = VIXAnalyzer.get_vix_level()
        market_sentiment = VIXAnalyzer.get_market_sentiment(vix_level) if vix_level else None
    except Exception as e:
        error_handler.logger.warning(f"VIX數據獲取失敗: {e}")
        vix_level = None
        market_sentiment = None
    
    # 獲取投資組合建議 - 非關鍵數據，錯誤時繼續
    try:
        portfolio_analysis = strategy_engine.get_portfolio_strategy_analysis(strategy_name)
        portfolio_suggestions = portfolio_analysis.get('rebalance_suggestions', [])
    except Exception as e:
        error_handler.logger.warning(f"投資組合分析失敗: {e}")
        portfolio_suggestions = []
    
    return jsonify({
        'success': True,
        'data': signals_data['signals'],
        'strategy_used': signals_data['strategy_used'],
        'vix_level': vix_level,
        'market_sentiment': market_sentiment,
        'portfolio_suggestions': portfolio_suggestions,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/signals/multi/<symbol>')
def get_multi_strategy_signals(symbol):
    """API端點：獲取特定股票的多策略信號"""
    try:
        symbol = symbol.upper()
        multi_signals = strategy_engine.generate_signals_multiple_strategies(symbol)
        
        if 'error' in multi_signals:
            return jsonify({
                'success': False,
                'error': multi_signals['error'],
                'timestamp': datetime.now().isoformat()
            }), 500
        
        return jsonify({
            'success': True,
            'data': multi_signals,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/strategy/compare')
def compare_strategies():
    """API端點：比較不同策略的預期表現"""
    try:
        time_horizon = int(request.args.get('time_horizon', 1))
        comparison = strategy_engine.compare_strategy_performance(time_horizon)
        
        return jsonify({
            'success': True,
            'data': comparison,
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
        strategy_name = request.args.get('strategy')
        portfolio_data = strategy_engine.get_portfolio_strategy_analysis(strategy_name)
        
        return jsonify({
            'success': True,
            'analysis': portfolio_data['portfolio_analysis'],
            'expected_returns': portfolio_data['expected_returns'],
            'strategy_used': portfolio_data['strategy_used'],
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
        strategy_name = request.args.get('strategy')
        portfolio_data = strategy_engine.get_portfolio_strategy_analysis(strategy_name)
        
        return jsonify({
            'success': True,
            'suggestions': portfolio_data['rebalance_suggestions'],
            'strategy_used': portfolio_data['strategy_used'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/stocks/monitored')
def get_monitored_stocks():
    """API端點：獲取監控股票列表"""
    try:
        monitored = strategy_engine.get_monitored_stocks()
        
        # 添加股票名稱，創建新的格式化數據
        formatted_monitored = {}
        for region, stocks in monitored.items():
            formatted_monitored[region] = []
            for symbol in stocks:
                formatted_monitored[region].append({
                    'symbol': symbol,
                    'name': STOCK_NAMES.get(symbol, symbol)
                })
        
        return jsonify({
            'success': True,
            'data': formatted_monitored,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/stocks/add', methods=['POST'])
def add_monitored_stock():
    """API端點：添加監控股票"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        region = data.get('region')
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': '缺少股票代號參數'
            }), 400
        
        success = strategy_engine.add_monitored_stock(symbol, region)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'成功添加{symbol}到監控列表',
                'symbol': symbol,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': f'無法添加{symbol}，可能是無效的股票代號',
                'timestamp': datetime.now().isoformat()
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/stocks/remove', methods=['DELETE'])
def remove_monitored_stock():
    """API端點：移除監控股票"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': '缺少股票代號參數'
            }), 400
        
        success = strategy_engine.remove_monitored_stock(symbol)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'成功從監控列表移除{symbol}',
                'symbol': symbol,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': f'{symbol}不在監控列表中',
                'timestamp': datetime.now().isoformat()
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/stock/<symbol>')
def get_stock_detail(symbol):
    """API端點：獲取特定股票詳細信息"""
    try:
        symbol = symbol.upper()
        analyzer = StockAnalyzer(symbol)
        
        if not analyzer.fetch_data():
            return jsonify({
                'success': False,
                'error': f'無法獲取{symbol}的數據'
            }), 404
        
        # 獲取歷史數據和技術指標
        sma_20 = analyzer.calculate_sma(20)
        sma_50 = analyzer.calculate_sma(50)
        rsi = analyzer.calculate_rsi()
        macd, macd_signal, macd_histogram = analyzer.calculate_macd()
        upper_bb, middle_bb, lower_bb = analyzer.calculate_bollinger_bands()
        
        # 準備圖表數據
        chart_data = {
            'dates': analyzer.data.index.strftime('%Y-%m-%d').tolist(),
            'prices': analyzer.data['Close'].tolist(),
            'sma_20': sma_20.tolist() if sma_20 is not None else [],
            'sma_50': sma_50.tolist() if sma_50 is not None else [],
            'rsi': rsi.tolist() if rsi is not None else [],
            'macd': macd.tolist() if macd is not None else [],
            'macd_signal': macd_signal.tolist() if macd_signal is not None else [],
            'upper_bb': upper_bb.tolist() if upper_bb is not None else [],
            'lower_bb': lower_bb.tolist() if lower_bb is not None else [],
            'volume': analyzer.data['Volume'].tolist()
        }
        
        # 獲取多策略信號
        multi_signals = strategy_engine.generate_signals_multiple_strategies(symbol)
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'name': STOCK_NAMES.get(symbol, symbol),
            'chart_data': chart_data,
            'multi_strategy_signals': multi_signals,
            'current_price': analyzer.get_current_price(),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404錯誤處理"""
    return jsonify({
        'success': False,
        'error': 'API端點不存在',
        'timestamp': datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500錯誤處理"""
    return jsonify({
        'success': False,
        'error': '伺服器內部錯誤',
        'timestamp': datetime.now().isoformat()
    }), 500

@app.route('/api/risk-management/<symbol>')
def get_risk_management(symbol):
    """API端點：獲取特定股票的風險管理建議"""
    try:
        # 獲取股票數據
        analyzer = StockAnalyzer(symbol)
        if not analyzer.fetch_data():
            return jsonify({
                'success': False,
                'error': '股票數據獲取失敗',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        current_price = analyzer.get_current_price()
        if not current_price:
            return jsonify({
                'success': False,
                'error': '無法獲取當前價格',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # 獲取當前活躍策略的風險等級
        active_strategy = strategy_engine.get_active_strategy()
        risk_level = getattr(active_strategy, 'risk_level', 'medium') if active_strategy else 'medium'
        
        # 計算風險管理方案
        risk_plans = risk_manager.get_comprehensive_risk_plan(
            current_price, analyzer.data, risk_level
        )
        
        return jsonify({
            'success': True,
            'data': risk_plans,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/risk-management/batch')
def get_batch_risk_management():
    """API端點：獲取所有監控股票的風險管理建議"""
    try:
        monitored_stocks = strategy_engine.get_monitored_stocks()
        active_strategy = strategy_engine.get_active_strategy()
        risk_level = getattr(active_strategy, 'risk_level', 'medium') if active_strategy else 'medium'
        
        batch_results = {}
        
        # 處理所有區域的股票
        for region, stocks in monitored_stocks.items():
            batch_results[region] = {}
            
            for symbol in stocks:
                try:
                    analyzer = StockAnalyzer(symbol)
                    if analyzer.fetch_data():
                        current_price = analyzer.get_current_price()
                        if current_price:
                            risk_plans = risk_manager.get_comprehensive_risk_plan(
                                current_price, analyzer.data, risk_level
                            )
                            batch_results[region][symbol] = {
                                'success': True,
                                'data': risk_plans
                            }
                        else:
                            batch_results[region][symbol] = {
                                'success': False,
                                'error': '無法獲取當前價格'
                            }
                    else:
                        batch_results[region][symbol] = {
                            'success': False,
                            'error': '數據獲取失敗'
                        }
                except Exception as e:
                    batch_results[region][symbol] = {
                        'success': False,
                        'error': str(e)
                    }
        
        return jsonify({
            'success': True,
            'data': batch_results,
            'strategy_risk_level': risk_level,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/chart-data/<symbol>')
def get_chart_data(symbol):
    """API端點：獲取圖表數據"""
    try:
        # 獲取期間參數
        period = request.args.get('period', '3mo')  # 預設3個月
        
        # 獲取股票數據
        analyzer = StockAnalyzer(symbol)
        if not analyzer.fetch_data(period=period):
            return jsonify({
                'success': False,
                'error': '股票數據獲取失敗',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # 計算技術指標
        sma_20 = analyzer.calculate_sma(20)
        sma_200 = analyzer.calculate_sma(200)
        rsi = analyzer.calculate_rsi()
        
        # 準備圖表數據
        data = analyzer.data.copy()
        
        # 添加技術指標
        if sma_20 is not None:
            data['SMA_20'] = sma_20
        if sma_200 is not None:
            data['SMA_200'] = sma_200
        if rsi is not None:
            data['RSI'] = rsi
        
        # 獲取當前活躍策略的交易信號
        active_strategy = strategy_engine.get_active_strategy()
        trading_signals = []
        
        if active_strategy:
            try:
                # 獲取最近的信號點
                recent_data = data.tail(60)  # 最近60天
                for i in range(len(recent_data)):
                    temp_data = data.head(len(data) - len(recent_data) + i + 1)
                    temp_analyzer = StockAnalyzer(symbol)
                    temp_analyzer.data = temp_data
                    
                    signal_result = active_strategy.generate_signal(temp_analyzer, symbol=symbol)
                    if signal_result.get('signal') in ['BUY', 'SELL']:
                        trading_signals.append({
                            'date': recent_data.index[i].isoformat(),
                            'price': float(recent_data.iloc[i]['Close']),
                            'signal': signal_result['signal'],
                            'confidence': signal_result.get('confidence', 0)
                        })
            except Exception as e:
                print(f"計算交易信號失敗: {e}")
        
        # 格式化數據為Chart.js格式
        chart_data = {
            'labels': [date.strftime('%Y-%m-%d') for date in data.index],
            'datasets': [],
            'trading_signals': trading_signals
        }
        
        # 添加價格數據
        chart_data['datasets'].append({
            'label': f'{symbol} 收盤價',
            'data': [{'x': date.strftime('%Y-%m-%d'), 'y': float(price)} 
                    for date, price in zip(data.index, data['Close'])],
            'borderColor': '#2563eb',
            'backgroundColor': 'rgba(37, 99, 235, 0.1)',
            'fill': True,
            'tension': 0.1,
            'yAxisID': 'y'
        })
        
        # 添加SMA20
        if 'SMA_20' in data.columns:
            chart_data['datasets'].append({
                'label': 'SMA 20',
                'data': [{'x': date.strftime('%Y-%m-%d'), 'y': float(sma) if not pd.isna(sma) else None} 
                        for date, sma in zip(data.index, data['SMA_20'])],
                'borderColor': '#f59e0b',
                'backgroundColor': 'transparent',
                'fill': False,
                'tension': 0.1,
                'yAxisID': 'y'
            })
        
        # 添加SMA200
        if 'SMA_200' in data.columns:
            chart_data['datasets'].append({
                'label': 'SMA 200',
                'data': [{'x': date.strftime('%Y-%m-%d'), 'y': float(sma) if not pd.isna(sma) else None} 
                        for date, sma in zip(data.index, data['SMA_200'])],
                'borderColor': '#dc2626',
                'backgroundColor': 'transparent',
                'fill': False,
                'tension': 0.1,
                'yAxisID': 'y'
            })
        
        # 添加RSI數據（使用第二個Y軸）
        if 'RSI' in data.columns:
            chart_data['datasets'].append({
                'label': 'RSI',
                'data': [{'x': date.strftime('%Y-%m-%d'), 'y': float(rsi) if not pd.isna(rsi) else None} 
                        for date, rsi in zip(data.index, data['RSI'])],
                'borderColor': '#8b5cf6',
                'backgroundColor': 'rgba(139, 92, 246, 0.1)',
                'fill': False,
                'tension': 0.1,
                'yAxisID': 'y1'
            })
        
        return jsonify({
            'success': True,
            'data': chart_data,
            'symbol': symbol,
            'period': period,
            'current_price': float(analyzer.get_current_price()) if analyzer.get_current_price() else None,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    print("🚀 啟動股票監控系統 v2.0")
    print(f"📊 已載入{len(strategy_engine.get_available_strategies())}個交易策略")
    print(f"📈 監控{len(strategy_engine.monitored_stocks['US']) + len(strategy_engine.monitored_stocks['TW'])}支股票")
    print("🌐 服務器運行在 http://localhost:5001")
    
    app.run(
        debug=FLASK_CONFIG['DEBUG'],
        host=FLASK_CONFIG['HOST'], 
        port=5001  # 使用不同端口避免衝突
    )