// 修復buy_hold策略顯示問題

(function() {
    // 監聽策略切換
    const originalSwitchStrategy = window.stockMonitor?.switchStrategy;
    
    if (window.stockMonitor && originalSwitchStrategy) {
        window.stockMonitor.switchStrategy = async function(strategyName) {
            console.log(`切換到策略: ${strategyName}`);
            
            // 調用原始方法
            const result = await originalSwitchStrategy.call(this, strategyName);
            
            // 如果是buy_hold策略，確保正確渲染
            if (strategyName === 'buy_hold') {
                console.log('特殊處理buy_hold策略顯示...');
                
                // 強制重新載入信號
                setTimeout(async () => {
                    try {
                        const response = await fetch('/api/signals?strategy=buy_hold');
                        const data = await response.json();
                        
                        if (data.success && data.data) {
                            console.log(`載入${data.data.length}個buy_hold信號`);
                            this.renderEnhancedSignals(data.data);
                        }
                    } catch (error) {
                        console.error('修復buy_hold顯示失敗:', error);
                    }
                }, 500);
            }
            
            return result;
        };
    }
    
    console.log('✅ buy_hold顯示修復已載入');
})();