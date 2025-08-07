#!/usr/bin/env python3
"""測試台股ETF代號"""

import yfinance as yf

# 測試台股主要ETF
etfs_to_test = [
    ("0050.TW", "台灣50"),
    ("0056.TW", "元大高股息"),     # 這個可能是你想要的高股息ETF
    ("0057.TW", "富邦台50"),
    ("006208.TW", "富邦台50"),
    ("00878.TW", "國泰永續高股息"),  # 這個可能是正確的00878
    ("00713.TW", "元大台灣高息低波"),
]

for symbol, name in etfs_to_test:
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="5d")
        if not data.empty:
            price = data['Close'].iloc[-1]
            print(f"✅ {symbol} ({name}): NT${price:.2f}")
        else:
            print(f"❌ {symbol} ({name}): 無數據")
    except Exception as e:
        print(f"❌ {symbol} ({name}): 錯誤")