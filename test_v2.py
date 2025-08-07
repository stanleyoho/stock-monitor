#!/usr/bin/env python3
"""
Stock Monitor System v2.0 Test
測試多策略系統功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.multi_strategy_engine import MultiStrategyEngine
from modules.stock_analyzer import StockAnalyzer, VIXAnalyzer
from strategies.momentum_strategy import MomentumStrategy
from strategies.mean_reversion_strategy import MeanReversionStrategy
from strategies.buy_hold_strategy import BuyHoldStrategy

def test_multi_strategy_system():
    """測試多策略系統"""
    print("🧪 開始測試股票監控系統 v2.0...")
    
    # 測試1: 多策略引擎初始化
    print("\n1. 測試多策略引擎初始化...")
    try:
        engine = MultiStrategyEngine()
        strategies = engine.get_available_strategies()
        print(f"✅ 多策略引擎初始化成功")
        print(f"   載入了{len(strategies)}個策略:")
        for name, info in strategies.items():
            print(f"   - {name}: {info['description']} (風險: {info['risk_level']})")
    except Exception as e:
        print(f"❌ 多策略引擎初始化失敗: {e}")
        return False
    
    # 測試2: 策略切換功能
    print("\n2. 測試策略切換...")
    try:
        success = engine.switch_strategy('mean_reversion')
        if success:
            print("✅ 策略切換成功: momentum -> mean_reversion")
        else:
            print("❌ 策略切換失敗")
    except Exception as e:
        print(f"❌ 策略切換測試失敗: {e}")
    
    # 測試3: 多策略信號生成
    print("\n3. 測試多策略信號生成...")
    try:
        signals_data = engine.generate_signals_all_stocks()
        if 'signals' in signals_data:
            signals = signals_data['signals']
            print(f"✅ 多策略信號生成成功")
            print(f"   生成了{len(signals)}個股票信號")
            print(f"   使用策略: {signals_data['strategy_used']}")
            
            # 顯示前3個信號
            for signal in signals[:3]:
                if not signal.get('error'):
                    print(f"   {signal['symbol']}: {signal['signal']} (信心度: {signal['confidence']:.1%})")
                else:
                    print(f"   {signal['symbol']}: ERROR - {signal.get('reasons', ['未知錯誤'])[0]}")
        else:
            print("❌ 信號生成失敗: 無信號數據")
    except Exception as e:
        print(f"❌ 多策略信號生成測試失敗: {e}")
    
    # 測試4: 單股多策略分析
    print("\n4. 測試單股多策略分析...")
    try:
        multi_signals = engine.generate_signals_multiple_strategies('NVDA')
        if 'consensus' in multi_signals:
            consensus = multi_signals['consensus']
            individual = multi_signals['individual_strategies']
            print(f"✅ 單股多策略分析成功")
            print(f"   NVDA策略共識: {consensus['signal']} (信心度: {consensus['confidence']:.1%})")
            print(f"   投票結果: {consensus['buy_votes']}買/{consensus['sell_votes']}賣/{consensus['hold_votes']}持有")
            print(f"   個別策略:")
            for strategy_name, signal in individual.items():
                if not signal.get('error'):
                    print(f"     {strategy_name}: {signal.get('signal', 'UNKNOWN')} ({signal.get('confidence', 0):.1%})")
        else:
            print("❌ 單股多策略分析失敗")
    except Exception as e:
        print(f"❌ 單股多策略分析測試失敗: {e}")
    
    # 測試5: 策略比較
    print("\n5. 測試策略表現比較...")
    try:
        comparison = engine.compare_strategy_performance(1)
        if 'ranking' in comparison:
            ranking = comparison['ranking']
            print(f"✅ 策略表現比較成功")
            print("   策略排名 (按風險調整後報酬):")
            for i, item in enumerate(ranking):
                strategy = item['strategy']
                data = item['data']
                expected_return = data['expected_annual_return'] * 100
                risk_adjusted = data['risk_adjusted_return'] * 100
                print(f"   {i+1}. {strategy}: {expected_return:.1f}% (風險調整: {risk_adjusted:.1f}%)")
        else:
            print("❌ 策略比較失敗")
    except Exception as e:
        print(f"❌ 策略比較測試失敗: {e}")
    
    # 測試6: 動態股票管理
    print("\n6. 測試動態股票管理...")
    try:
        # 添加股票
        success = engine.add_monitored_stock('AAPL')
        if success:
            print("✅ 成功添加 AAPL 到監控列表")
        
        # 檢查監控列表
        monitored = engine.get_monitored_stocks()
        total_stocks = len(monitored['US']) + len(monitored['TW'])
        print(f"   當前監控{total_stocks}支股票")
        
        # 移除股票
        success = engine.remove_monitored_stock('AAPL')
        if success:
            print("✅ 成功從監控列表移除 AAPL")
    except Exception as e:
        print(f"❌ 動態股票管理測試失敗: {e}")
    
    # 測試7: VIX和市場情緒
    print("\n7. 測試VIX恐慌指數和市場情緒...")
    try:
        vix_level = VIXAnalyzer.get_vix_level()
        if vix_level:
            sentiment = VIXAnalyzer.get_market_sentiment(vix_level)
            print(f"✅ VIX和市場情緒獲取成功")
            print(f"   VIX水平: {vix_level:.1f}")
            print(f"   市場情緒: {sentiment['label']}")
        else:
            print("⚠️  VIX數據獲取失敗，但不影響系統運行")
    except Exception as e:
        print(f"❌ VIX和市場情緒測試失敗: {e}")
    
    # 測試8: 投資組合策略分析
    print("\n8. 測試投資組合策略分析...")
    try:
        portfolio_analysis = engine.get_portfolio_strategy_analysis('momentum')
        if 'expected_returns' in portfolio_analysis:
            returns = portfolio_analysis['expected_returns']
            total_value = returns['current_value']
            annual_return = returns['expected_annual_return'] * 100
            print(f"✅ 投資組合策略分析成功")
            print(f"   總投資價值: ${total_value:,.0f}")
            print(f"   動量策略預期年化報酬: {annual_return:.1f}%")
            print(f"   1年後預期價值: ${returns['projected_value_1y']:,.0f}")
        else:
            print("❌ 投資組合策略分析失敗")
    except Exception as e:
        print(f"❌ 投資組合策略分析測試失敗: {e}")

def test_individual_strategies():
    """測試個別策略"""
    print("\n" + "="*50)
    print("🎯 測試個別策略實現")
    print("="*50)
    
    strategies = [
        ('動量策略', MomentumStrategy()),
        ('均值回歸策略', MeanReversionStrategy()),
        ('買入持有策略', BuyHoldStrategy())
    ]
    
    test_symbol = 'NVDA'
    analyzer = StockAnalyzer(test_symbol)
    
    if not analyzer.fetch_data():
        print(f"❌ 無法獲取{test_symbol}數據，跳過個別策略測試")
        return
    
    print(f"使用{test_symbol}測試各策略:")
    
    for name, strategy in strategies:
        try:
            signal = strategy.generate_signal(analyzer, symbol=test_symbol)
            expected_return = strategy.calculate_expected_return(test_symbol, analyzer.get_current_price())
            
            print(f"\n📊 {name}:")
            print(f"   信號: {signal['signal']} (信心度: {signal['confidence']:.1%})")
            print(f"   預期年化報酬: {expected_return*100:.1f}%")
            if signal['reasons']:
                print(f"   原因: {signal['reasons'][0]}")
        except Exception as e:
            print(f"❌ {name}測試失敗: {e}")

def main():
    """主測試函數"""
    print("=" * 60)
    print("📊 Stock Monitor v2.0 多策略系統測試")
    print("=" * 60)
    
    test_multi_strategy_system()
    test_individual_strategies()
    
    print("\n" + "=" * 60)
    print("🎉 測試完成！")
    print("💡 如果看到上述✅標誌，表示系統運作正常")
    print("🚀 可以運行 python app_v2.py 啟動完整的v2.0系統")
    print("🌐 或使用原版: python app.py")
    print("=" * 60)

if __name__ == "__main__":
    main()