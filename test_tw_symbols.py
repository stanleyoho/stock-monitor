#!/usr/bin/env python3
"""測試台股代號格式"""

import yfinance as yf

# 測試不同的台股代號格式
symbols_to_test = [
    "0050.TW",     # .TW 格式
    "0050.TWO",    # .TWO 格式  
    "0878.TW",     # .TW 格式
    "0878.TWO",    # .TWO 格式
    "2330.TW",     # 台積電 .TW
    "2330.TWO"     # 台積電 .TWO
]

for symbol in symbols_to_test:
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="5d")
        if not data.empty:
            price = data['Close'].iloc[-1]
            print(f"✅ {symbol}: ${price:.2f}")
        else:
            print(f"❌ {symbol}: 無數據")
    except Exception as e:
        print(f"❌ {symbol}: {e}")