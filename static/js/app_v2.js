// 股票監控應用v2.0 JavaScript - 支援多策略系統

class StockMonitorV2 {
    constructor() {
        this.charts = {};
        this.updateInterval = null;
        this.advancedView = false;
        this.portfolioData = null;
        this.currentStrategy = null;
        this.availableStrategies = {};
        this.isLoadingStrategy = false;
        this.init();
    }

    async init() {
        console.log('初始化股票監控應用 v2.0');
        await this.loadStrategies();
        await this.loadSignals();
        await this.loadPortfolio();
        // 已移除股票圖表，不需要載入
        // await this.loadCharts();
        this.startAutoUpdate();
    }

    async loadStrategies() {
        try {
            const response = await fetch('/api/strategies');
            const data = await response.json();
            
            if (data.success) {
                this.availableStrategies = data.strategies;
                this.renderStrategySelector();
                
                // 設置當前策略
                for (const [name, strategy] of Object.entries(data.strategies)) {
                    if (strategy.is_active) {
                        this.currentStrategy = name;
                        break;
                    }
                }
                
                this.updateCurrentStrategyDisplay();
            } else {
                console.error('載入策略失敗:', data.error);
            }
        } catch (error) {
            console.error('策略API請求失敗:', error);
        }
    }

    renderStrategySelector() {
        const container = document.getElementById('strategySelector');
        
        if (!this.availableStrategies || Object.keys(this.availableStrategies).length === 0) {
            container.innerHTML = '<div class="alert alert-warning">無可用策略</div>';
            return;
        }

        let html = '';
        
        for (const [name, strategy] of Object.entries(this.availableStrategies)) {
            const isActive = strategy.is_active;
            const riskColors = {
                'low': 'success',
                'medium': 'warning', 
                'high': 'danger'
            };
            const riskColor = riskColors[strategy.risk_level] || 'secondary';
            const riskLabel = {
                'low': '低風險',
                'medium': '中風險',
                'high': '高風險'
            }[strategy.risk_level] || strategy.risk_level;
            
            html += `
                <div class="col-lg-4 mb-3">
                    <div class="strategy-card ${isActive ? 'active' : ''}" onclick="switchStrategy('${name}')">
                        ${isActive ? '<div class="strategy-active-indicator"><i class="fas fa-check"></i></div>' : ''}
                        <div class="strategy-content">
                            <div class="strategy-header">
                                <h6 class="strategy-title">${strategy.name.toUpperCase()}</h6>
                            </div>
                            <div class="strategy-risk">
                                <span class="badge bg-${riskColor} badge-risk">${riskLabel}</span>
                            </div>
                            <p class="strategy-description">${strategy.description}</p>
                        </div>
                    </div>
                </div>
            `;
        }
        
        container.innerHTML = html;
    }

    async switchStrategy(strategyName) {
        // 防止重複切換
        if (this.isLoadingStrategy) {
            console.log('策略切換進行中，請稍候...');
            return;
        }
        
        this.isLoadingStrategy = true;
        this.showStrategyLoading(true);
        
        try {
            const response = await fetch('/api/strategy/switch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    strategy_name: strategyName
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentStrategy = strategyName;
                
                // 更新策略選擇器顯示
                this.availableStrategies[strategyName].is_active = true;
                for (const name of Object.keys(this.availableStrategies)) {
                    if (name !== strategyName) {
                        this.availableStrategies[name].is_active = false;
                    }
                }
                
                this.renderStrategySelector();
                this.updateCurrentStrategyDisplay();
                
                // 重新載入信號和投資組合
                try {
                    await this.loadSignals();
                } catch (loadError) {
                    console.error(`載入${strategyName}策略信號失敗:`, loadError);
                }
                
                try {
                    await this.loadPortfolio();
                } catch (portfolioError) {
                    console.error(`載入投資組合失敗:`, portfolioError);
                }
                
                this.showToast(`已切換至${strategyName}策略`, 'success');
            } else {
                this.showToast(`策略切換失敗: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('切換策略失敗:', error);
            this.showToast('策略切換失敗', 'error');
        } finally {
            this.isLoadingStrategy = false;
            this.showStrategyLoading(false);
        }
    }

    showStrategyLoading(show) {
        const selector = document.getElementById('strategySelector');
        if (show) {
            // 添加loading覆蓋層
            const loadingOverlay = document.createElement('div');
            loadingOverlay.id = 'strategyLoadingOverlay';
            loadingOverlay.className = 'position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
            loadingOverlay.style.background = 'rgba(255, 255, 255, 0.9)';
            loadingOverlay.style.zIndex = '1000';
            loadingOverlay.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">切換策略中...</span>
                    </div>
                    <p class="mt-2">正在切換策略...</p>
                </div>
            `;
            
            const parentElement = selector.closest('.card-body');
            if (parentElement) {
                parentElement.style.position = 'relative';
                parentElement.appendChild(loadingOverlay);
            }
        } else {
            // 移除loading覆蓋層
            const overlay = document.getElementById('strategyLoadingOverlay');
            if (overlay) {
                overlay.remove();
            }
        }
    }
    
    updateCurrentStrategyDisplay() {
        const element = document.getElementById('currentStrategy');
        if (element && this.currentStrategy) {
            element.textContent = this.availableStrategies[this.currentStrategy]?.name?.toUpperCase() || this.currentStrategy;
        }
        
    }

    getRiskAlertClass(riskLevel) {
        const mapping = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger'
        };
        return mapping[riskLevel] || 'secondary';
    }

    async loadSignals() {
        try {
            const url = this.currentStrategy ? 
                `/api/signals?strategy=${this.currentStrategy}` : 
                '/api/signals';
                
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                try {
                    this.renderEnhancedSignals(data.data);
                    this.updateMarketOverview(data.vix_level, data.market_sentiment);
                    this.updateRebalanceAlert(data.portfolio_suggestions);
                    this.updateLastUpdateTime(data.timestamp);
                } catch (renderError) {
                    console.error('渲染信號時發生錯誤:', renderError);
                    console.error('錯誤堆疊:', renderError.stack);
                    console.error('問題數據:', data.data);
                    this.showError('顯示信號時發生錯誤: ' + renderError.message);
                }
            } else {
                console.error('載入信號失敗:', data.error);
                this.showError('載入交易信號失敗');
            }
        } catch (error) {
            console.error('API請求失敗:', error);
            console.error('錯誤詳情:', error.message);
            this.showError('網路連接失敗，請檢查連接');
        }
    }

    renderEnhancedSignals(signals) {
        const container = document.getElementById('signalsContainer');
        
        if (!signals || signals.length === 0) {
            container.innerHTML = '<div class="alert alert-info">暫無交易信號</div>';
            return;
        }

        // 使用緊湊的表格式佈局
        let html = `
            <div class="table-responsive">
                <table class="signals-table">
                    <thead>
                        <tr>
                            <th>股票</th>
                            <th>價格</th>
                            <th>信號</th>
                            <th>SMA20</th>
                            <th>RSI</th>
                            <th>信心度</th>
                            <th>主要原因</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        signals.forEach(signal => {
            const signalClass = signal.signal ? signal.signal.toLowerCase() : 'hold';
            const signalIcon = this.getSignalIcon(signal.signal || 'HOLD');
            const confidencePercent = ((signal.confidence || 0) * 100).toFixed(0);
            
            // 處理錯誤信號
            if (signal.error) {
                html += this.renderErrorSignalCompact(signal);
                return;
            }
            
            // 取得主要原因
            const mainReason = signal.reasons && signal.reasons.length > 0 ? 
                signal.reasons[0].substring(0, 50) + (signal.reasons[0].length > 50 ? '...' : '') : 
                '持續監控';
            
            html += `
                <tr>
                    <td class="table-signal-symbol">
                        <div>${signal.symbol}</div>
                        <div class="strategy-tag strategy-${signal.strategy || 'unknown'}">${(signal.strategy || 'unknown').toUpperCase()}</div>
                    </td>
                    <td class="table-signal-price">${this.formatPrice(signal.current_price)}</td>
                    <td>
                        <span class="table-signal-badge signal-${signalClass}">${signalIcon} ${signal.signal || 'HOLD'}</span>
                    </td>
                    <td class="table-indicators">${this.formatPrice(signal.sma_20)}</td>
                    <td class="table-indicators">${signal.rsi ? signal.rsi.toFixed(1) : 'N/A'}</td>
                    <td class="table-indicators">
                        <div>${confidencePercent}%</div>
                        <div class="confidence-bar" style="width: 60px; height: 3px; background: #e0e0e0; margin-top: 2px;">
                            <div class="confidence-fill" style="width: ${confidencePercent}%; height: 100%; background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #10b981 100%);"></div>
                        </div>
                    </td>
                    <td class="table-indicators" style="max-width: 200px;">
                        <small>${mainReason}</small>
                        ${signal.reasons && signal.reasons.length > 1 ? 
                            `<br><small class="text-muted">+${signal.reasons.length - 1} more</small>` : ''}
                    </td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        
        // 添加詳細信息展開面板（可選）
        html += '<div class="mt-3"><small class="text-muted">點擊股票代號可查看詳細技術指標</small></div>';
        
        container.innerHTML = html;
        
        // 添加點擊事件來顯示詳細信息
        this.addSignalDetailListeners(signals);
    }

    renderErrorSignalCompact(signal) {
        const errorReason = signal.reasons && signal.reasons.length > 0 ? 
            signal.reasons[0] : '未知錯誤';
        
        return `
            <tr style="background: #fff5f5;">
                <td class="table-signal-symbol">
                    <div>${signal.symbol}</div>
                    <div class="badge bg-danger">ERROR</div>
                </td>
                <td class="table-signal-price">--</td>
                <td>
                    <span class="table-signal-badge bg-danger text-white">⚠️ ERROR</span>
                </td>
                <td class="table-indicators">--</td>
                <td class="table-indicators">--</td>
                <td class="table-indicators">--</td>
                <td class="table-indicators">
                    <small class="text-danger">${errorReason}</small>
                </td>
            </tr>
        `;
    }
    
    addSignalDetailListeners(signals) {
        // 為股票代號添加點擊事件，顯示詳細技術指標
        const symbolElements = document.querySelectorAll('.table-signal-symbol');
        symbolElements.forEach((element, index) => {
            element.style.cursor = 'pointer';
            element.addEventListener('click', () => {
                this.showSignalDetails(signals[index]);
            });
        });
    }
    
    showSignalDetails(signal) {
        if (signal.error) return;
        
        let detailsHtml = `
            <div class="modal fade" id="signalDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${signal.symbol} 詳細分析與風險管理</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <!-- 技術指標 -->
                            <h6>技術指標</h6>
                            <div class="indicators-grid">
                                <div class="indicator-mini">
                                    <div class="indicator-mini-label">當前價格</div>
                                    <div class="indicator-mini-value">${this.formatPrice(signal.current_price)}</div>
                                </div>
                                <div class="indicator-mini">
                                    <div class="indicator-mini-label">SMA 20</div>
                                    <div class="indicator-mini-value">${this.formatPrice(signal.sma_20)}</div>
                                </div>
                                <div class="indicator-mini">
                                    <div class="indicator-mini-label">RSI</div>
                                    <div class="indicator-mini-value">${signal.rsi ? signal.rsi.toFixed(1) : 'N/A'}</div>
                                </div>
                                ${signal.sma_200 ? `
                                <div class="indicator-mini">
                                    <div class="indicator-mini-label">SMA 200</div>
                                    <div class="indicator-mini-value">${this.formatPrice(signal.sma_200)}</div>
                                </div>
                                ` : ''}
                                ${signal.vix_level ? `
                                <div class="indicator-mini">
                                    <div class="indicator-mini-label">VIX</div>
                                    <div class="indicator-mini-value">${signal.vix_level.toFixed(1)}</div>
                                </div>
                                ` : ''}
                                <div class="indicator-mini">
                                    <div class="indicator-mini-label">信心度</div>
                                    <div class="indicator-mini-value">${((signal.confidence || 0) * 100).toFixed(0)}%</div>
                                </div>
                            </div>
                            
                            <!-- 分析原因 -->
                            <div class="mt-4">
                                <h6>分析原因：</h6>
                                <ul class="list-unstyled">
                                    ${signal.reasons && signal.reasons.length > 0 ? 
                                        signal.reasons.map(reason => `<li><small>• ${reason}</small></li>`).join('') 
                                        : '<li><small>無特殊訊號</small></li>'}
                                </ul>
                            </div>
                            
                            <!-- 風險管理建議 -->
                            <div class="mt-4">
                                <h6>風險管理建議</h6>
                                <div id="riskManagementContent">載入中...</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 移除現有的 modal
        const existingModal = document.getElementById('signalDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // 添加新的 modal
        document.body.insertAdjacentHTML('beforeend', detailsHtml);
        const modal = new bootstrap.Modal(document.getElementById('signalDetailsModal'));
        modal.show();
        
        // 載入風險管理信息
        this.loadRiskManagement(signal.symbol);
    }
    
    async loadRiskManagement(symbol) {
        const content = document.getElementById('riskManagementContent');
        
        try {
            const response = await fetch(`/api/risk-management/${symbol}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderRiskManagement(data.data);
            } else {
                content.innerHTML = `<div class="alert alert-warning">風險管理資料載入失敗: ${data.error}</div>`;
            }
        } catch (error) {
            console.error('載入風險管理失敗:', error);
            content.innerHTML = '<div class="alert alert-danger">風險管理資料載入失敗</div>';
        }
    }
    
    renderRiskManagement(riskData) {
        const content = document.getElementById('riskManagementContent');
        
        let html = `
            <div class="row">
                <div class="col-12 mb-3">
                    <div class="alert alert-info">
                        <strong>建議方案：</strong> ${riskData.plans[riskData.recommendation.recommended_plan].name}
                        <br><small>${riskData.recommendation.reason}</small>
                    </div>
                </div>
            </div>
        `;
        
        // 顯示所有風險管理方案
        html += '<div class="row">';
        
        Object.entries(riskData.plans).forEach(([planKey, plan]) => {
            const isRecommended = planKey === riskData.recommendation.recommended_plan;
            
            html += `
                <div class="col-md-6 mb-3">
                    <div class="card ${isRecommended ? 'border-primary' : ''}">
                        <div class="card-header ${isRecommended ? 'bg-primary text-white' : 'bg-light'}">
                            <h6 class="mb-0">
                                ${plan.name} ${isRecommended ? '(推薦)' : ''}
                            </h6>
                            <small>${plan.description}</small>
                        </div>
                        <div class="card-body">
                            <!-- 停損資訊 -->
                            <div class="mb-2">
                                <strong>停損策略：</strong> ${plan.stop_loss.type}
                                <br>
                                <span class="text-danger">停損價: ${this.formatPrice(plan.stop_loss.price)} (-${plan.stop_loss.percentage.toFixed(1)}%)</span>
                                <br>
                                <small class="text-muted">${plan.stop_loss.reasoning}</small>
                            </div>
                            
                            <!-- 停利資訊 -->
                            <div class="mb-2">
                                <strong>停利策略：</strong> ${plan.take_profit.type}
                                <br>
                                <span class="text-success">停利價: ${this.formatPrice(plan.take_profit.price)} (+${plan.take_profit.percentage.toFixed(1)}%)</span>
                                <br>
                                <small class="text-muted">${plan.take_profit.reasoning}</small>
                            </div>
                            
                            <!-- 適用對象 -->
                            <div class="mt-2">
                                <span class="badge bg-${plan.risk_level === 'low' ? 'success' : plan.risk_level === 'high' ? 'danger' : 'warning'}">${plan.risk_level.toUpperCase()}</span>
                                <br>
                                <small><strong>適合：</strong> ${plan.suitability}</small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        
        content.innerHTML = html;
    }
    
    async showRiskManagementPanel() {
        const panel = document.getElementById('riskManagementPanel');
        const content = document.getElementById('riskManagementContent');
        
        panel.style.display = 'block';
        content.innerHTML = `
            <div class="text-center">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">載入中...</span>
                </div>
                <p class="mt-2">正在計算風險管理方案...</p>
            </div>
        `;
        
        try {
            const response = await fetch('/api/risk-management/batch');
            const data = await response.json();
            
            if (data.success) {
                this.renderBatchRiskManagement(data.data, data.strategy_risk_level);
            } else {
                content.innerHTML = `<div class="alert alert-danger">風險管理資料載入失敗: ${data.error}</div>`;
            }
        } catch (error) {
            console.error('載入風險管理失敗:', error);
            content.innerHTML = '<div class="alert alert-danger">風險管理資料載入失敗</div>';
        }
    }
    
    renderBatchRiskManagement(batchData, strategyRiskLevel) {
        const content = document.getElementById('riskManagementContent');
        
        let html = `
            <div class="alert alert-info mb-4">
                <strong>當前策略風險等級：</strong> ${strategyRiskLevel.toUpperCase()}
                <br><small>風險管理建議已根據您的策略風險等級進行調整</small>
            </div>
        `;
        
        // 處理每個區域的股票
        Object.entries(batchData).forEach(([region, stocks]) => {
            html += `
                <div class="mb-4">
                    <h6>${region === 'US' ? '美股' : '台股'} 風險管理建議</h6>
                    <div class="row">
            `;
            
            Object.entries(stocks).forEach(([symbol, result]) => {
                if (result.success && result.data) {
                    const riskData = result.data;
                    const recommendedPlan = riskData.plans[riskData.recommendation.recommended_plan];
                    
                    html += `
                        <div class="col-lg-6 mb-3">
                            <div class="card">
                                <div class="card-header">
                                    <h6 class="mb-0">${symbol} - ${recommendedPlan.name}</h6>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-6">
                                            <strong>停損價</strong>
                                            <br>
                                            <span class="text-danger">${this.formatPrice(recommendedPlan.stop_loss.price)}</span>
                                            <br>
                                            <small class="text-muted">-${recommendedPlan.stop_loss.percentage.toFixed(1)}%</small>
                                        </div>
                                        <div class="col-6">
                                            <strong>停利價</strong>
                                            <br>
                                            <span class="text-success">${this.formatPrice(recommendedPlan.take_profit.price)}</span>
                                            <br>
                                            <small class="text-muted">+${recommendedPlan.take_profit.percentage.toFixed(1)}%</small>
                                        </div>
                                    </div>
                                    <div class="mt-2">
                                        <button class="btn btn-sm btn-outline-primary" onclick="window.stockMonitor.showDetailedRiskPlan('${symbol}', ${JSON.stringify(riskData).replace(/"/g, '&quot;')})">
                                            查看詳細方案
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    html += `
                        <div class="col-lg-6 mb-3">
                            <div class="card border-warning">
                                <div class="card-body text-center">
                                    <h6>${symbol}</h6>
                                    <div class="text-warning">
                                        ${result.error || '資料獲取失敗'}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }
            });
            
            html += '</div></div>';
        });
        
        content.innerHTML = html;
    }
    
    showDetailedRiskPlan(symbol, riskDataString) {
        // 解析風險數據
        const riskData = JSON.parse(riskDataString.replace(/&quot;/g, '"'));
        
        let detailsHtml = `
            <div class="modal fade" id="riskPlanDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${symbol} 完整風險管理方案</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
        `;
        
        // 顯示所有方案
        detailsHtml += this.formatRiskPlansForModal(riskData);
        
        detailsHtml += `
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">關閉</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 移除現有modal並添加新的
        const existingModal = document.getElementById('riskPlanDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', detailsHtml);
        const modal = new bootstrap.Modal(document.getElementById('riskPlanDetailsModal'));
        modal.show();
    }
    
    formatRiskPlansForModal(riskData) {
        let html = `
            <div class="alert alert-info">
                <strong>建議方案：</strong> ${riskData.plans[riskData.recommendation.recommended_plan].name}
                <br><small>${riskData.recommendation.reason}</small>
            </div>
            <div class="row">
        `;
        
        Object.entries(riskData.plans).forEach(([planKey, plan]) => {
            const isRecommended = planKey === riskData.recommendation.recommended_plan;
            
            html += `
                <div class="col-md-6 mb-3">
                    <div class="card ${isRecommended ? 'border-primary' : ''}">
                        <div class="card-header ${isRecommended ? 'bg-primary text-white' : 'bg-light'}">
                            <strong>${plan.name} ${isRecommended ? '(推薦)' : ''}</strong>
                            <br><small>${plan.description}</small>
                        </div>
                        <div class="card-body">
                            <div class="mb-2">
                                <strong>停損：</strong> ${plan.stop_loss.type}
                                <br>
                                <span class="text-danger">${this.formatPrice(plan.stop_loss.price)} (-${plan.stop_loss.percentage.toFixed(1)}%)</span>
                            </div>
                            <div class="mb-2">
                                <strong>停利：</strong> ${plan.take_profit.type}
                                <br>
                                <span class="text-success">${this.formatPrice(plan.take_profit.price)} (+${plan.take_profit.percentage.toFixed(1)}%)</span>
                            </div>
                            <div>
                                <span class="badge bg-${plan.risk_level === 'low' ? 'success' : plan.risk_level === 'high' ? 'danger' : 'warning'}">${plan.risk_level.toUpperCase()}</span>
                                <br><small><strong>適合：</strong> ${plan.suitability}</small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }
    
    hideRiskManagementPanel() {
        document.getElementById('riskManagementPanel').style.display = 'none';
    }
    
    toggleChartsView() {
        const panel = document.getElementById('chartsPanel');
        const toggleText = document.getElementById('chartsToggleText');
        
        if (panel.style.display === 'none') {
            panel.style.display = 'block';
            toggleText.textContent = '隱藏圖表';
            this.initializeCharts();
        } else {
            panel.style.display = 'none';
            toggleText.textContent = '顯示圖表';
        }
    }
    
    async initializeCharts() {
        // 載入股票選項
        try {
            const response = await fetch('/api/stocks/monitored');
            const data = await response.json();
            
            if (data.success) {
                const selector = document.getElementById('chartStockSelector');
                selector.innerHTML = '<option value="">選擇股票</option>';
                
                // 添加所有監控的股票
                Object.entries(data.data).forEach(([region, stocks]) => {
                    const optgroup = document.createElement('optgroup');
                    optgroup.label = region === 'US' ? '美股' : '台股';
                    
                    stocks.forEach(stock => {
                        const option = document.createElement('option');
                        option.value = stock.symbol;
                        option.textContent = `${stock.symbol} - ${stock.name}`;
                        optgroup.appendChild(option);
                    });
                    
                    selector.appendChild(optgroup);
                });
                
                // 預設選擇第一檔股票
                if (data.data.US && data.data.US.length > 0) {
                    const firstStock = data.data.US[0].symbol;
                    selector.value = firstStock;
                    this.loadStockChart(firstStock);
                }
            }
        } catch (error) {
            console.error('載入股票列表失敗:', error);
        }
    }
    
    switchChartStock(symbol) {
        if (symbol) {
            this.loadStockChart(symbol);
        }
    }
    
    async loadStockChart(symbol) {
        const container = document.getElementById('stockChartsContainer');
        
        // 顯示載入狀態
        container.innerHTML = `
            <div class="text-center">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">載入中...</span>
                </div>
                <p class="mt-2">正在載入 ${symbol} 圖表數據...</p>
            </div>
        `;
        
        try {
            const response = await fetch(`/api/chart-data/${symbol}?period=3mo`);
            const data = await response.json();
            
            if (data.success) {
                this.renderStockChart(data.data, data.symbol, data.current_price);
            } else {
                container.innerHTML = `<div class="alert alert-danger">圖表數據載入失敗: ${data.error}</div>`;
            }
        } catch (error) {
            console.error('載入圖表數據失敗:', error);
            container.innerHTML = '<div class="alert alert-danger">圖表數據載入失敗</div>';
        }
    }
    
    renderStockChart(chartData, symbol, currentPrice) {
        const container = document.getElementById('stockChartsContainer');
        
        // 創建圖表容器
        container.innerHTML = `
            <div class="row">
                <div class="col-12 mb-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6>${symbol} 股價走勢</h6>
                        <div class="text-end">
                            <div class="h5 mb-0">$${currentPrice ? currentPrice.toFixed(2) : 'N/A'}</div>
                            <small class="text-muted">當前價格</small>
                        </div>
                    </div>
                </div>
                <div class="col-12">
                    <canvas id="stockChart" style="height: 400px;"></canvas>
                </div>
            </div>
        `;
        
        // 銷毀現有圖表
        if (this.currentChart) {
            this.currentChart.destroy();
        }
        
        // 創建新圖表
        const ctx = document.getElementById('stockChart').getContext('2d');
        
        this.currentChart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            parser: 'YYYY-MM-DD',
                            tooltipFormat: 'YYYY-MM-DD',
                            displayFormats: {
                                day: 'MM-DD',
                                week: 'MM-DD',
                                month: 'YYYY-MM'
                            }
                        },
                        title: {
                            display: true,
                            text: '日期'
                        }
                    },
                    y: {
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: '股價 ($)'
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        title: {
                            display: true,
                            text: 'RSI'
                        },
                        min: 0,
                        max: 100,
                        grid: {
                            drawOnChartArea: false
                        },
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            title: function(context) {
                                return new Date(context[0].label).toLocaleDateString('zh-TW');
                            },
                            label: function(context) {
                                const label = context.dataset.label || '';
                                if (label.includes('RSI')) {
                                    return `${label}: ${context.parsed.y.toFixed(1)}%`;
                                } else {
                                    return `${label}: $${context.parsed.y.toFixed(2)}`;
                                }
                            }
                        }
                    },
                    annotation: {
                        annotations: this.createSignalAnnotations(chartData.trading_signals)
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }
    
    createSignalAnnotations(tradingSignals) {
        const annotations = {};
        
        // 添加RSI參考線
        annotations.rsiOverbought = {
            type: 'line',
            yMin: 70,
            yMax: 70,
            yScaleID: 'y1',
            borderColor: 'red',
            borderWidth: 1,
            borderDash: [5, 5],
            label: {
                content: 'RSI 70 (超買)',
                enabled: true,
                position: 'end'
            }
        };
        
        annotations.rsiOversold = {
            type: 'line',
            yMin: 30,
            yMax: 30,
            yScaleID: 'y1',
            borderColor: 'green',
            borderWidth: 1,
            borderDash: [5, 5],
            label: {
                content: 'RSI 30 (超賣)',
                enabled: true,
                position: 'end'
            }
        };
        
        // 添加交易信號點
        if (tradingSignals && tradingSignals.length > 0) {
            tradingSignals.forEach((signal, index) => {
                annotations[`signal_${index}`] = {
                    type: 'point',
                    xValue: signal.date,
                    yValue: signal.price,
                    backgroundColor: signal.signal === 'BUY' ? '#10b981' : '#ef4444',
                    borderColor: signal.signal === 'BUY' ? '#10b981' : '#ef4444',
                    borderWidth: 2,
                    radius: 6,
                    label: {
                        content: `${signal.signal} (${(signal.confidence * 100).toFixed(0)}%)`,
                        enabled: true,
                        position: 'top'
                    }
                };
            });
        }
        
        return annotations;
    }

    async compareStrategies() {
        const panel = document.getElementById('strategyComparisonPanel');
        const content = document.getElementById('strategyComparisonContent');
        
        panel.style.display = 'block';
        content.innerHTML = `
            <div class="text-center">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">計算中...</span>
                </div>
                <p class="mt-2">正在比較策略表現...</p>
            </div>
        `;
        
        try {
            const response = await fetch('/api/strategy/compare?time_horizon=1');
            const data = await response.json();
            
            if (data.success) {
                this.renderStrategyComparison(data.data);
            } else {
                content.innerHTML = `<div class="alert alert-danger">策略比較失敗: ${data.error}</div>`;
            }
        } catch (error) {
            console.error('策略比較失敗:', error);
            content.innerHTML = '<div class="alert alert-danger">策略比較失敗</div>';
        }
    }

    renderStrategyComparison(comparisonData) {
        const content = document.getElementById('strategyComparisonContent');
        
        let html = '<div class="row">';
        
        // 策略排名
        if (comparisonData.ranking && comparisonData.ranking.length > 0) {
            html += '<div class="col-12 mb-4">';
            html += '<h6>策略排名 (按風險調整後報酬)</h6>';
            html += '<div class="row">';
            
            comparisonData.ranking.forEach((item, index) => {
                const strategy = item.strategy;
                const data = item.data;
                const medalEmojis = ['🥇', '🥈', '🥉'];
                const medal = medalEmojis[index] || `${index + 1}.`;
                
                html += `
                    <div class="col-md-4 mb-3">
                        <div class="card strategy-rank-card">
                            <div class="card-body text-center">
                                <div class="strategy-rank">${medal}</div>
                                <h6>${strategy.toUpperCase()}</h6>
                                <div class="metric-row">
                                    <span class="metric-label">預期報酬:</span>
                                    <span class="metric-value text-success">${(data.expected_annual_return * 100).toFixed(1)}%</span>
                                </div>
                                <div class="metric-row">
                                    <span class="metric-label">風險調整:</span>
                                    <span class="metric-value">${(data.risk_adjusted_return * 100).toFixed(1)}%</span>
                                </div>
                                <div class="metric-row">
                                    <span class="metric-label">風險等級:</span>
                                    <span class="badge bg-${this.getRiskBadgeColor(data.risk_score)}">${data.risk_level?.toUpperCase()}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div></div>';
        }
        
        // 詳細比較表
        html += '<div class="col-12">';
        html += '<h6>詳細比較</h6>';
        html += '<div class="table-responsive">';
        html += '<table class="table table-striped">';
        html += '<thead><tr><th>策略</th><th>預期年化報酬</th><th>風險等級</th><th>風險調整後報酬</th><th>建議</th></tr></thead>';
        html += '<tbody>';
        
        for (const [strategy, data] of Object.entries(comparisonData.comparison)) {
            const returnPct = (data.expected_annual_return * 100).toFixed(1);
            const riskAdjustedPct = (data.risk_adjusted_return * 100).toFixed(1);
            const recommendation = this.getStrategyRecommendation(data);
            
            html += `
                <tr>
                    <td><strong>${strategy.toUpperCase()}</strong></td>
                    <td><span class="text-success">${returnPct}%</span></td>
                    <td><span class="badge bg-${this.getRiskBadgeColor(data.risk_score)}">${data.risk_level?.toUpperCase()}</span></td>
                    <td><strong>${riskAdjustedPct}%</strong></td>
                    <td><small>${recommendation}</small></td>
                </tr>
            `;
        }
        
        html += '</tbody></table>';
        html += '</div></div>';
        html += '</div>';
        
        content.innerHTML = html;
    }

    getStrategyRecommendation(data) {
        const riskLevel = data.risk_level;
        const expectedReturn = data.expected_annual_return;
        
        if (expectedReturn > 0.15 && riskLevel === 'high') {
            return '高報酬但高風險，適合積極投資者';
        } else if (expectedReturn > 0.10 && riskLevel === 'medium') {
            return '平衡型投資，報酬與風險適中';
        } else if (riskLevel === 'low') {
            return '穩健型投資，適合保守投資者';
        } else {
            return '請評估個人風險承受度';
        }
    }

    getRiskBadgeColor(riskScore) {
        if (riskScore <= 0.8) return 'success';
        if (riskScore <= 1.2) return 'warning';
        return 'danger';
    }

    hideStrategyComparison() {
        document.getElementById('strategyComparisonPanel').style.display = 'none';
    }

    async showStockManager() {
        const modal = new bootstrap.Modal(document.getElementById('stockManagerModal'));
        await this.loadCurrentStocks();
        modal.show();
    }

    async loadCurrentStocks() {
        const container = document.getElementById('currentStocksList');
        
        try {
            const response = await fetch('/api/stocks/monitored');
            const data = await response.json();
            
            if (data.success) {
                this.renderStocksList(data.data);
            } else {
                container.innerHTML = '<div class="alert alert-danger">載入失敗</div>';
            }
        } catch (error) {
            console.error('載入股票列表失敗:', error);
            container.innerHTML = '<div class="alert alert-danger">載入失敗</div>';
        }
    }

    renderStocksList(stocksData) {
        const container = document.getElementById('currentStocksList');
        let html = '';
        
        for (const [region, stocks] of Object.entries(stocksData)) {
            html += `<h6 class="mt-3">${region === 'US' ? '美股' : '台股'}</h6>`;
            html += '<div class="row">';
            
            stocks.forEach(stock => {
                const symbol = typeof stock === 'string' ? stock : stock.symbol;
                const name = typeof stock === 'string' ? stock : (stock.name || stock.symbol);
                
                html += `
                    <div class="col-md-6 mb-2">
                        <div class="d-flex justify-content-between align-items-center">
                            <span><strong>${symbol}</strong> - ${name}</span>
                            <button class="btn btn-sm btn-outline-danger" onclick="removeStock('${symbol}')">移除</button>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
        }
        
        container.innerHTML = html;
    }

    async addStock() {
        const symbol = document.getElementById('newStockSymbol').value.trim().toUpperCase();
        
        if (!symbol) {
            this.showToast('請輸入股票代號', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/stocks/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: symbol
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast(`成功添加${symbol}`, 'success');
                document.getElementById('newStockSymbol').value = '';
                await this.loadCurrentStocks();
                // 重新載入信號
                await this.loadSignals();
            } else {
                this.showToast(`添加失敗: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('添加股票失敗:', error);
            this.showToast('添加股票失敗', 'error');
        }
    }

    async removeStock(symbol) {
        if (!confirm(`確定要移除${symbol}嗎？`)) {
            return;
        }
        
        try {
            const response = await fetch('/api/stocks/remove', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: symbol
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast(`成功移除${symbol}`, 'success');
                await this.loadCurrentStocks();
                // 重新載入信號
                await this.loadSignals();
            } else {
                this.showToast(`移除失敗: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('移除股票失敗:', error);
            this.showToast('移除股票失敗', 'error');
        }
    }

    // 繼承原有功能
    async loadPortfolio() {
        try {
            const url = this.currentStrategy ? 
                `/api/portfolio?strategy=${this.currentStrategy}` : 
                '/api/portfolio';
                
            const response = await fetch(url);
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
            sentimentElement.textContent = marketSentiment.label || marketSentiment;
            sentimentElement.className = `indicator-value sentiment-${marketSentiment.sentiment?.toLowerCase()}`;
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
                    <strong>📊 1年後可能區間 (基於${this.currentStrategy || '當前'}策略):</strong><br>
                    樂觀情境: <span class="text-success">${this.formatCurrency(expectedReturns.best_case_1y)}</span> | 
                    悲觀情境: <span class="text-danger">${this.formatCurrency(expectedReturns.worst_case_1y)}</span><br>
                    <small>* 預期報酬基於選定策略和歷史數據，實際結果可能有所不同</small>
                </div>
            </div>
        `;
        
        html += '</div>';
        container.innerHTML = html;
    }

    async loadCharts() {
        const stocks = ['QQQ', 'NVDA', 'VOO'];
        
        for (const stock of stocks) {
            try {
                const response = await fetch(`/api/stock/${stock}`);
                const data = await response.json();
                
                if (data.success) {
                    this.createChart(stock, data.chart_data, data.multi_strategy_signals?.consensus);
                    this.updateStockDetail(stock, data.multi_strategy_signals?.consensus);
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

        if (!chartData || !chartData.dates || chartData.dates.length === 0) {
            ctx.getContext('2d').fillText('無數據', 100, 100);
            return;
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

        const signalClass = signal.signal ? signal.signal.toLowerCase() : 'hold';
        const signalIcon = this.getSignalIcon(signal.signal || 'HOLD');

        detailElement.innerHTML = `
            <div class="indicator mb-2">
                <span class="indicator-label">當前信號:</span>
                <span class="indicator-value signal-badge signal-${signalClass}">${signalIcon} ${signal.signal || 'HOLD'}</span>
            </div>
            <div class="row">
                <div class="col-6">
                    <div class="indicator">
                        <div class="indicator-label">價格</div>
                        <div class="indicator-value">${this.formatPrice(signal.current_price)}</div>
                    </div>
                </div>
                <div class="col-6">
                    <div class="indicator">
                        <div class="indicator-label">信心度</div>
                        <div class="indicator-value">${((signal.confidence || 0) * 100).toFixed(0)}%</div>
                    </div>
                </div>
            </div>
            ${signal.buy_votes !== undefined ? `
                <div class="mt-2">
                    <small class="text-muted">策略共識: ${signal.buy_votes}買/${signal.sell_votes}賣/${signal.hold_votes}持有</small>
                </div>
            ` : ''}
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
            await this.loadPortfolio();
        }, 5 * 60 * 1000);
    }

    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
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
    }

    showError(message) {
        const container = document.getElementById('signalsContainer');
        container.innerHTML = `
            <div class="alert alert-danger">
                <strong>錯誤:</strong> ${message}
                <button type="button" class="btn btn-sm btn-outline-danger ms-2" onclick="stockMonitor.refresh()">
                    重新載入
                </button>
            </div>
        `;
    }

    showToast(message, type = 'info') {
        // 簡單的提示實現
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger', 
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        const toast = document.createElement('div');
        toast.className = `alert ${alertClass} position-fixed`;
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        toast.style.minWidth = '300px';
        toast.innerHTML = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    getSignalIcon(signal) {
        switch (signal) {
            case 'BUY': return '🟢';
            case 'SELL': return '🔴';
            case 'HOLD': return '🟡';
            default: return '⚪';
        }
    }

    formatCurrency(amount) {
        if (!amount) return 'N/A';
        if (amount >= 1000000) {
            return `$${(amount / 1000000).toFixed(1)}M`;
        } else if (amount >= 1000) {
            return `$${(amount / 1000).toFixed(0)}K`;
        } else {
            return `$${amount.toFixed(0)}`;
        }
    }

    formatPrice(price) {
        if (!price) return 'N/A';
        return `$${price.toFixed(2)}`;
    }

    showToast(message, type = 'info') {
        // 創建或獲取toast容器
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }

        // 創建toast元素
        const toastId = 'toast-' + Date.now();
        const iconMap = {
            'success': 'fas fa-check-circle text-success',
            'error': 'fas fa-times-circle text-danger',
            'warning': 'fas fa-exclamation-circle text-warning',
            'info': 'fas fa-info-circle text-info'
        };

        const toastHtml = `
            <div class="toast" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <i class="${iconMap[type] || iconMap.info} me-2"></i>
                    <strong class="me-auto">系統通知</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        // 顯示toast
        const toastElement = document.getElementById(toastId);
        if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
            const toast = new bootstrap.Toast(toastElement, {
                autohide: true,
                delay: type === 'error' ? 5000 : 3000
            });
            
            toast.show();
            
            // 自動清理
            toastElement.addEventListener('hidden.bs.toast', () => {
                toastElement.remove();
            });
        } else {
            // 如果Bootstrap不可用，使用簡單的顯示方式
            toastElement.style.display = 'block';
            setTimeout(() => {
                toastElement.remove();
            }, type === 'error' ? 5000 : 3000);
        }
    }
}

// 初始化應用 - 使用window對象避免重複聲明
document.addEventListener('DOMContentLoaded', function() {
    window.stockMonitor = new StockMonitorV2();
    
    // 添加快捷鍵支持
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'r') {
            e.preventDefault();
            window.stockMonitor.refresh();
        }
    });
});

// 頁面卸載時停止自動更新
window.addEventListener('beforeunload', function() {
    if (window.stockMonitor) {
        window.stockMonitor.stopAutoUpdate();
    }
});

// 全局函數
function refreshData() {
    if (window.stockMonitor) {
        window.stockMonitor.refresh();
    }
}

function toggleAdvancedView() {
    if (window.stockMonitor) {
        window.stockMonitor.toggleAdvancedView();
    }
}

function switchStrategy(strategyName) {
    if (window.stockMonitor) {
        window.stockMonitor.switchStrategy(strategyName);
    }
}

function compareStrategies() {
    if (window.stockMonitor) {
        window.stockMonitor.compareStrategies();
    }
}

function hideStrategyComparison() {
    if (window.stockMonitor) {
        window.stockMonitor.hideStrategyComparison();
    }
}

function showStockManager() {
    if (window.stockMonitor) {
        window.stockMonitor.showStockManager();
    }
}

function addStock() {
    if (window.stockMonitor) {
        window.stockMonitor.addStock();
    }
}

function removeStock(symbol) {
    if (window.stockMonitor) {
        window.stockMonitor.removeStock(symbol);
    }
}

