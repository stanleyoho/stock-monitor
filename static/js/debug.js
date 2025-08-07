// 調試腳本 - 診斷buy_hold策略顯示問題

async function debugBuyHoldDisplay() {
    console.log('=== 開始診斷buy_hold策略顯示問題 ===');
    
    // 1. 檢查API響應
    console.log('1. 檢查API響應...');
    const response = await fetch('/api/signals?strategy=buy_hold');
    const data = await response.json();
    console.log('API成功:', data.success);
    console.log('信號數量:', data.data?.length);
    console.log('第一個信號:', data.data?.[0]);
    
    // 2. 檢查DOM元素
    console.log('\n2. 檢查DOM元素...');
    const container = document.getElementById('signalsContainer');
    console.log('signalsContainer存在:', !!container);
    console.log('容器內容長度:', container?.innerHTML?.length);
    
    // 3. 檢查StockMonitorV2實例
    console.log('\n3. 檢查StockMonitorV2實例...');
    console.log('window.stockMonitor存在:', !!window.stockMonitor);
    console.log('當前策略:', window.stockMonitor?.currentStrategy);
    console.log('可用策略:', window.stockMonitor?.availableStrategies);
    
    // 4. 手動調用渲染方法
    console.log('\n4. 嘗試手動渲染...');
    if (window.stockMonitor && data.data) {
        try {
            window.stockMonitor.renderEnhancedSignals(data.data);
            console.log('✅ 手動渲染成功');
        } catch (error) {
            console.error('❌ 渲染錯誤:', error);
            console.error('錯誤堆疊:', error.stack);
        }
    }
    
    // 5. 檢查錯誤信號
    console.log('\n5. 檢查錯誤信號...');
    const errorSignals = data.data?.filter(s => s.error);
    console.log('錯誤信號數量:', errorSignals?.length || 0);
    if (errorSignals?.length > 0) {
        console.log('錯誤信號詳情:', errorSignals);
    }
    
    // 6. 檢查方法是否存在
    console.log('\n6. 檢查必要方法...');
    console.log('renderEnhancedSignals:', typeof window.stockMonitor?.renderEnhancedSignals);
    console.log('getSignalIcon:', typeof window.stockMonitor?.getSignalIcon);
    console.log('formatPrice:', typeof window.stockMonitor?.formatPrice);
    console.log('renderErrorSignal:', typeof window.stockMonitor?.renderErrorSignal);
    
    console.log('\n=== 診斷完成 ===');
}

// 頁面載入後執行診斷
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(debugBuyHoldDisplay, 2000);
    });
} else {
    setTimeout(debugBuyHoldDisplay, 2000);
}