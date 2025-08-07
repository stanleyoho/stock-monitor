#!/usr/bin/env python3
"""
Stock Monitor System Test
簡單測試腳本來驗證系統功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import PortfolioManager, StrategySignalGenerator, StockAnalyzer

def test_basic_functionality():
    """測試基本功能"""
    print("🧪 開始測試Stock Monitor系統...")
    
    # 測試1: StockAnalyzer
    print("\n1. 測試股票分析器...")
    try:
        analyzer = StockAnalyzer("AAPL")
        if analyzer.fetch_data():
            print("✅ 股票數據獲取成功")
            price = analyzer.data['Close'].iloc[-1]
            print(f"   AAPL當前價格: ${price:.2f}")
        else:
            print("❌ 股票數據獲取失敗")
    except Exception as e:
        print(f"❌ StockAnalyzer測試失敗: {e}")
    
    # 測試2: PortfolioManager
    print("\n2. 測試投資組合管理器...")
    try:
        portfolio = PortfolioManager()
        analysis = portfolio.get_portfolio_analysis()
        if analysis:
            total_value = analysis['total_value']['total']
            print(f"✅ 投資組合分析成功")
            print(f"   總投資價值: ${total_value:,.2f}")
        else:
            print("❌ 投資組合分析失敗")
    except Exception as e:
        print(f"❌ PortfolioManager測試失敗: {e}")
    
    # 測試3: StrategySignalGenerator
    print("\n3. 測試策略信號生成器...")
    try:
        signal_gen = StrategySignalGenerator()
        signals = signal_gen.get_enhanced_signals()
        if signals and 'signals' in signals:
            print("✅ 交易信號生成成功")
            print(f"   生成了{len(signals['signals'])}個股票信號")
            for signal in signals['signals'][:2]:  # 只顯示前2個
                print(f"   {signal['symbol']}: {signal['signal']} (信心度: {signal['confidence']:.1%})")
        else:
            print("❌ 交易信號生成失敗")
    except Exception as e:
        print(f"❌ StrategySignalGenerator測試失敗: {e}")
    
    # 測試4: 預期報酬計算
    print("\n4. 測試預期報酬計算...")
    try:
        portfolio = PortfolioManager()
        returns = portfolio.calculate_expected_returns()
        if returns:
            print("✅ 預期報酬計算成功")
            annual_return = returns['expected_annual_return'] * 100
            print(f"   預期年化報酬: {annual_return:.1f}%")
            print(f"   1年後預期價值: ${returns['projected_value_1y']:,.0f}")
        else:
            print("❌ 預期報酬計算失敗")
    except Exception as e:
        print(f"❌ 預期報酬計算測試失敗: {e}")

def test_portfolio_rebalancing():
    """測試投資組合再平衡建議"""
    print("\n5. 測試動態平衡建議...")
    try:
        portfolio = PortfolioManager()
        suggestions = portfolio.get_rebalance_suggestions()
        if suggestions:
            print(f"✅ 再平衡建議生成成功")
            print(f"   生成了{len(suggestions)}個調整建議")
            for suggestion in suggestions[:3]:  # 只顯示前3個
                action = "買入" if suggestion['action'] == 'BUY' else "賣出"
                print(f"   {action} {suggestion['symbol']}: ${suggestion['amount']:,.0f}")
        else:
            print("✅ 當前無需再平衡")
    except Exception as e:
        print(f"❌ 再平衡建議測試失敗: {e}")

def main():
    """主測試函數"""
    print("=" * 50)
    print("📊 Stock Monitor 整合系統測試")
    print("=" * 50)
    
    test_basic_functionality()
    test_portfolio_rebalancing()
    
    print("\n" + "=" * 50)
    print("🎉 測試完成！")
    print("💡 如果看到上述✅標誌，表示系統運作正常")
    print("🚀 可以運行 ./start.sh 啟動完整系統")
    print("=" * 50)

if __name__ == "__main__":
    main()