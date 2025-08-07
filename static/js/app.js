// 股票監控應用JavaScript

class StockMonitor {
    constructor() {
        this.charts = {};
        this.updateInterval = null;
        this.advancedView = false;
        this.portfolioData = null;
        this.init();
    }

    async init() {
        console.log('初始化股票監控應用');
        await this.loadSignals();
        await this.loadPortfolio();
        await this.loadCharts();
        this.startAutoUpdate();
    }

    async loadSignals() {
        try {
            const response = await fetch('/api/signals');
            const data = await response.json();
            
            if (data.success) {
                this.renderEnhancedSignals(data.data);
                this.updateMarketOverview(data.vix_level, data.market_sentiment);
                this.updateRebalanceAlert(data.portfolio_suggestions);
                this.updateLastUpdateTime(data.timestamp);
            } else {
                console.error('載入信號失敗:', data.error);
                this.showError('載入交易信號失敗');
            }
        } catch (error) {
            console.error('API請求失敗:', error);
            this.showError('網路連接失敗，請檢查連接');
        }
    }

    renderEnhancedSignals(signals) {
        const container = document.getElementById('signalsContainer');
        
        if (!signals || signals.length === 0) {
            container.innerHTML = '<div class="alert alert-info">暫無交易信號</div>';
            return;
        }

        let html = '<div class="row">';
        
        signals.forEach(signal => {
            const signalClass = signal.signal.toLowerCase();
            const signalIcon = this.getSignalIcon(signal.signal);
            const confidencePercent = (signal.confidence * 100).toFixed(0);
            
            html += `
                <div class="col-lg-6 mb-3">
                    <div class="enhanced-signal signal-${signalClass}">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div>
                                <h6 class="mb-0">${signal.symbol}</h6>
                                <span class="strategy-tag strategy-${signal.strategy}">${signal.strategy}</span>
                            </div>
                            <span class="signal-badge">${signalIcon} ${signal.signal}</span>
                        </div>
                        
                        <div class="stock-price">$${signal.current_price ? signal.current_price.toFixed(2) : 'N/A'}</div>
                        
                        <div class="row mt-2">
                            <div class="col-4">
                                <div class="indicator">
                                    <div class="indicator-label">SMA20</div>
                                    <div class="indicator-value">${signal.sma_20 ? '$' + signal.sma_20.toFixed(2) : 'N/A'}</div>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="indicator">
                                    <div class="indicator-label">RSI</div>
                                    <div class="indicator-value">${signal.rsi ? signal.rsi.toFixed(1) : 'N/A'}</div>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="indicator">
                                    <div class="indicator-label">信心度</div>
                                    <div class="indicator-value">${confidencePercent}%</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: ${confidencePercent}%"></div>
                        </div>
                        
                        <div class="mt-2">
                            ${signal.reasons && signal.reasons.length > 0 ? 
                                signal.reasons.map(reason => `<small class="text-muted d-block">• ${reason}</small>`).join('') 
                                : '<small class="text-muted">無特殊訊號</small>'}
                        </div>
                        
                        <div class="advanced-info">
                            <div class="row mt-2">
                                ${signal.stop_loss_price ? `
                                    <div class="col-6">
                                        <div class="indicator">
                                            <div class="indicator-label">停損價</div>
                                            <div class="indicator-value text-danger">$${signal.stop_loss_price.toFixed(2)}</div>
                                        </div>
                                    </div>
                                ` : ''}
                                ${signal.target_price ? `
                                    <div class="col-6">
                                        <div class="indicator">
                                            <div class="indicator-label">目標價</div>
                                            <div class="indicator-value text-success">$${signal.target_price.toFixed(2)}</div>
                                        </div>
                                    </div>
                                ` : ''}
                            </div>
                            ${signal.macd ? `
                                <div class="row mt-1">
                                    <div class="col-6">
                                        <div class="indicator">
                                            <div class="indicator-label">MACD</div>
                                            <div class="indicator-value">${signal.macd.toFixed(3)}</div>
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="indicator">
                                            <div class="indicator-label">SMA50</div>
                                            <div class="indicator-value">${signal.sma_50 ? '$' + signal.sma_50.toFixed(2) : 'N/A'}</div>
                                        </div>
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }

    async loadPortfolio() {
        try {
            const response = await fetch('/api/portfolio');
            const data = await response.json();
            
            if (data.success) {
                this.portfolioData = data;
                this.updatePortfolioOverview(data.analysis, data.expected_returns);
                this.renderReturnProjections(data.expected_returns);
            }
        } catch (error) {
            console.error('載入投資組合失敗:', error);
        }
    }

    updateMarketOverview(vixLevel, marketSentiment) {
        const vixElement = document.getElementById('vixLevel');
        const sentimentElement = document.getElementById('marketSentiment');
        
        if (vixElement && vixLevel) {
            vixElement.textContent = vixLevel.toFixed(1);
            vixElement.className = 'indicator-value';
            
            if (vixLevel > 30) {
                vixElement.classList.add('sentiment-panic');
            } else if (vixLevel > 20) {
                vixElement.classList.add('sentiment-fear');
            } else if (vixLevel > 15) {
                vixElement.classList.add('sentiment-neutral');
            } else {
                vixElement.classList.add('sentiment-greed');
            }
        }
        
        if (sentimentElement && marketSentiment) {
            const sentimentMap = {
                'panic': '😨 恐慌',
                'fear': '😰 恐懼',
                'neutral': '😐 中性',
                'greed': '🤑 貪婪'
            };
            sentimentElement.textContent = sentimentMap[marketSentiment] || marketSentiment;
            sentimentElement.className = `indicator-value sentiment-${marketSentiment}`;
        }
    }

    updatePortfolioOverview(analysis, expectedReturns) {
        const portfolioValueElement = document.getElementById('portfolioValue');
        const expectedReturnElement = document.getElementById('expectedReturn');
        
        if (portfolioValueElement && analysis && analysis.total_value) {
            const totalValue = analysis.total_value.total;
            portfolioValueElement.textContent = this.formatCurrency(totalValue);
        }
        
        if (expectedReturnElement && expectedReturns) {
            const annualReturn = expectedReturns.expected_annual_return * 100;
            expectedReturnElement.textContent = `${annualReturn.toFixed(1)}%`;
            expectedReturnElement.className = annualReturn > 0 ? 'indicator-value sentiment-greed' : 'indicator-value sentiment-fear';
        }
    }

    updateRebalanceAlert(suggestions) {
        const alertElement = document.getElementById('rebalanceAlert');
        const contentElement = document.getElementById('rebalanceContent');
        
        if (!suggestions || suggestions.length === 0) {
            alertElement.style.display = 'none';
            return;
        }
        
        let html = '<p><strong>建議進行以下調整:</strong></p>';
        suggestions.forEach(suggestion => {
            const actionClass = suggestion.action.toLowerCase() === 'buy' ? 'rebalance-buy' : 'rebalance-sell';
            const actionText = suggestion.action === 'BUY' ? '買入' : '賣出';
            
            html += `
                <div class="rebalance-suggestion">
                    <span class="rebalance-action ${actionClass}">${actionText}</span>
                    <strong>${suggestion.symbol}</strong> 
                    ${this.formatCurrency(suggestion.amount)}
                    <br><small>${suggestion.reason}</small>
                </div>
            `;
        });
        
        contentElement.innerHTML = html;
        alertElement.style.display = 'block';
    }

    renderReturnProjections(expectedReturns) {
        const container = document.getElementById('returnProjections');
        
        if (!expectedReturns) {
            container.innerHTML = '<div class="alert alert-warning">無法計算預期報酬</div>';
            return;
        }
        
        const projections = [
            { time: '1年後', value: expectedReturns.projected_value_1y, current: expectedReturns.current_value },
            { time: '3年後', value: expectedReturns.projected_value_3y, current: expectedReturns.current_value },
            { time: '5年後', value: expectedReturns.projected_value_5y, current: expectedReturns.current_value }
        ];
        
        let html = '<div class="row">';
        
        projections.forEach(proj => {
            const gain = proj.value - proj.current;
            const returnPercent = ((proj.value - proj.current) / proj.current * 100).toFixed(1);
            
            html += `
                <div class="col-md-4">
                    <div class="return-projection">
                        <div class="return-time">${proj.time}</div>
                        <div class="return-value">+${returnPercent}%</div>
                        <div class="return-amount">
                            ${this.formatCurrency(proj.value)}<br>
                            <small class="text-success">+${this.formatCurrency(gain)}</small>
                        </div>
                    </div>
                </div>
            `;
        });
        
        // 風險區間
        html += `
            <div class="col-12 mt-3">
                <div class="alert alert-info">
                    <strong>📊 1年後可能區間:</strong><br>
                    樂觀情境: <span class="text-success">${this.formatCurrency(expectedReturns.best_case_1y)}</span> | 
                    悲觀情境: <span class="text-danger">${this.formatCurrency(expectedReturns.worst_case_1y)}</span><br>
                    <small>* 預期報酬基於歷史數據，實際結果可能有所不同</small>
                </div>
            </div>
        `;
        
        html += '</div>';
        container.innerHTML = html;
    }

    formatCurrency(amount) {
        if (amount >= 1000000) {
            return `$${(amount / 1000000).toFixed(1)}M`;
        } else if (amount >= 1000) {
            return `$${(amount / 1000).toFixed(0)}K`;
        } else {
            return `$${amount.toFixed(0)}`;
        }
    }

    getSignalIcon(signal) {
        switch (signal) {
            case 'BUY': return '🟢';
            case 'SELL': return '🔴';
            case 'HOLD': return '🟡';
            default: return '⚪';
        }
    }

    async loadCharts() {
        const stocks = ['QQQ', 'NVDA', 'VOO'];
        
        for (const stock of stocks) {
            try {
                const response = await fetch(`/api/stock/${stock}`);
                const data = await response.json();
                
                if (data.success) {
                    this.createChart(stock, data.chart_data, data.signal);
                    this.updateStockDetail(stock, data.signal);
                } else {
                    console.error(`載入${stock}圖表失敗:`, data.error);
                }
            } catch (error) {
                console.error(`載入${stock}圖表時發生錯誤:`, error);
            }
        }
    }

    createChart(symbol, chartData, signal) {
        const ctx = document.getElementById(`chart${symbol}`);
        if (!ctx) {
            console.error(`找不到圖表元素: chart${symbol}`);
            return;
        }

        // 如果圖表已存在，先銷毀
        if (this.charts[symbol]) {
            this.charts[symbol].destroy();
        }

        const dates = chartData.dates.slice(-30); // 只顯示最近30天
        const prices = chartData.prices.slice(-30);
        const sma20 = chartData.sma_20.slice(-30);

        this.charts[symbol] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: '股價',
                        data: prices,
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.1
                    },
                    {
                        label: 'SMA20',
                        data: sma20,
                        borderColor: '#fd7e14',
                        backgroundColor: 'rgba(253, 126, 20, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.1,
                        borderDash: [5, 5]
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    title: {
                        display: true,
                        text: `${symbol} - 價格趨勢`
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '日期'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: '價格 ($)'
                        }
                    }
                }
            }
        });
    }

    updateStockDetail(symbol, signal) {
        const detailElement = document.getElementById(`detail${symbol}`);
        if (!detailElement || !signal) return;

        const signalClass = signal.signal.toLowerCase();
        const signalIcon = this.getSignalIcon(signal.signal);

        detailElement.innerHTML = `
            <div class="indicator mb-2">
                <span class="indicator-label">當前信號:</span>
                <span class="indicator-value signal-badge signal-${signalClass}">${signalIcon} ${signal.signal}</span>
            </div>
            <div class="row">
                <div class="col-6">
                    <div class="indicator">
                        <div class="indicator-label">價格</div>
                        <div class="indicator-value">$${signal.current_price.toFixed(2)}</div>
                    </div>
                </div>
                <div class="col-6">
                    <div class="indicator">
                        <div class="indicator-label">RSI</div>
                        <div class="indicator-value">${signal.rsi.toFixed(1)}</div>
                    </div>
                </div>
            </div>
        `;
    }

    updateLastUpdateTime(timestamp) {
        const updateElement = document.getElementById('lastUpdate');
        if (updateElement) {
            const date = new Date(timestamp);
            updateElement.textContent = date.toLocaleString('zh-TW');
        }
    }

    startAutoUpdate() {
        // 每5分鐘自動更新一次
        this.updateInterval = setInterval(async () => {
            console.log('自動更新數據...');
            await this.loadSignals();
            // 圖表不需要頻繁更新，只更新信號
        }, 5 * 60 * 1000);
    }

    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    showError(message) {
        const container = document.getElementById('signalsContainer');
        container.innerHTML = `
            <div class="alert alert-danger">
                <strong>錯誤:</strong> ${message}
                <button type="button" class="btn btn-sm btn-outline-danger ms-2" onclick="stockMonitor.loadSignals()">
                    重新載入
                </button>
            </div>
        `;
    }

    toggleAdvancedView() {
        this.advancedView = !this.advancedView;
        const signalsContainer = document.getElementById('signalsContainer');
        const toggleText = document.getElementById('advancedToggleText');
        
        if (this.advancedView) {
            signalsContainer.classList.add('show-advanced');
            toggleText.textContent = '隱藏詳細';
        } else {
            signalsContainer.classList.remove('show-advanced');
            toggleText.textContent = '顯示詳細';
        }
    }

    toggleStrategyInfo() {
        const panel = document.getElementById('strategyInfoPanel');
        const toggleText = document.getElementById('strategyToggleText');
        
        if (panel.style.display === 'none' || panel.style.display === '') {
            panel.style.display = 'block';
            toggleText.textContent = '隱藏說明';
        } else {
            panel.style.display = 'none';
            toggleText.textContent = '策略說明';
        }
    }

    // 手動重新整理
    async refresh() {
        console.log('手動重新整理...');
        const container = document.getElementById('signalsContainer');
        container.innerHTML = `
            <div class="text-center">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">載入中...</span>
                </div>
                <p class="mt-2">正在更新數據...</p>
            </div>
        `;
        
        await this.loadSignals();
        await this.loadPortfolio();
        await this.loadCharts();
    }
}

// 初始化應用
let stockMonitor;

document.addEventListener('DOMContentLoaded', function() {
    stockMonitor = new StockMonitor();
    
    // 添加快捷鍵支持
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'r') {
            e.preventDefault();
            stockMonitor.refresh();
        }
    });
});

// 頁面卸載時停止自動更新
window.addEventListener('beforeunload', function() {
    if (stockMonitor) {
        stockMonitor.stopAutoUpdate();
    }
});

// 全局函數
function refreshData() {
    if (stockMonitor) {
        stockMonitor.refresh();
    }
}

function toggleAdvancedView() {
    if (stockMonitor) {
        stockMonitor.toggleAdvancedView();
    }
}

function toggleStrategyInfo() {
    if (stockMonitor) {
        stockMonitor.toggleStrategyInfo();
    }
}