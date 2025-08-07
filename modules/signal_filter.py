"""
交易信號過濾器
用於減少雜訊信號，避免頻繁交易
"""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os

class SignalFilter:
    """交易信號過濾器"""
    
    def __init__(self, 
                 cooldown_hours: int = 4,
                 min_confidence_threshold: float = 0.6,
                 signal_confirmation_required: bool = True,
                 storage_file: str = 'signal_history.json'):
        """
        初始化信號過濾器
        
        Args:
            cooldown_hours: 信號冷卻時間（小時）
            min_confidence_threshold: 最小信心度閾值
            signal_confirmation_required: 是否需要信號確認
            storage_file: 信號歷史存儲文件
        """
        self.cooldown_hours = cooldown_hours
        self.min_confidence_threshold = min_confidence_threshold
        self.signal_confirmation_required = signal_confirmation_required
        self.storage_file = storage_file
        self.signal_history = self._load_signal_history()
    
    def _load_signal_history(self) -> Dict:
        """載入信號歷史"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"載入信號歷史失敗: {e}")
        
        return {}
    
    def _save_signal_history(self):
        """保存信號歷史"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.signal_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存信號歷史失敗: {e}")
    
    def should_emit_signal(self, symbol: str, new_signal: Dict) -> tuple[bool, str]:
        """
        判斷是否應該發出信號
        
        Args:
            symbol: 股票代號
            new_signal: 新的交易信號
            
        Returns:
            tuple: (是否發出信號, 原因)
        """
        if symbol not in self.signal_history:
            self.signal_history[symbol] = []
        
        current_time = datetime.now()
        signal_type = new_signal.get('signal', 'HOLD')
        confidence = new_signal.get('confidence', 0.0)
        
        # 檢查信心度閾值
        if confidence < self.min_confidence_threshold:
            return False, f"信心度{confidence:.1%}低於閾值{self.min_confidence_threshold:.1%}"
        
        # 如果是HOLD信號，通常不需要發出（除非從其他信號轉為HOLD）
        if signal_type == 'HOLD':
            recent_signals = self._get_recent_signals(symbol, hours=24)
            if not recent_signals or recent_signals[-1]['signal'] == 'HOLD':
                return False, "持續HOLD狀態，無需發出信號"
        
        # 檢查冷卻期
        if self._is_in_cooldown(symbol, signal_type, current_time):
            last_signal_time = self._get_last_signal_time(symbol, signal_type)
            return False, f"信號冷卻期內，上次{signal_type}信號時間: {last_signal_time}"
        
        # 檢查信號確認
        if self.signal_confirmation_required:
            if not self._is_signal_confirmed(symbol, new_signal):
                return False, "信號需要確認，等待下一次確認"
        
        # 檢查信號重複
        if self._is_duplicate_signal(symbol, signal_type, confidence):
            return False, "重複的信號類型和信心度"
        
        # 檢查信號反轉合理性
        if not self._is_signal_reversal_reasonable(symbol, signal_type):
            return False, "信號反轉過於頻繁，可能是雜訊"
        
        # 通過所有過濾條件，記錄新信號
        self._record_signal(symbol, new_signal, current_time)
        return True, "信號通過過濾條件"
    
    def _is_in_cooldown(self, symbol: str, signal_type: str, current_time: datetime) -> bool:
        """檢查是否在冷卻期內"""
        recent_signals = self._get_recent_signals(symbol, hours=self.cooldown_hours)
        
        for signal in recent_signals:
            if signal['signal'] == signal_type:
                return True
        
        return False
    
    def _get_last_signal_time(self, symbol: str, signal_type: str) -> Optional[str]:
        """獲取最後一次特定類型信號的時間"""
        if symbol not in self.signal_history:
            return None
        
        for signal in reversed(self.signal_history[symbol]):
            if signal['signal'] == signal_type:
                return signal['timestamp']
        
        return None
    
    def _get_recent_signals(self, symbol: str, hours: int = 24) -> List[Dict]:
        """獲取最近幾小時的信號"""
        if symbol not in self.signal_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_signals = []
        
        for signal in self.signal_history[symbol]:
            signal_time = datetime.fromisoformat(signal['timestamp'])
            if signal_time >= cutoff_time:
                recent_signals.append(signal)
        
        return recent_signals
    
    def _is_signal_confirmed(self, symbol: str, new_signal: Dict) -> bool:
        """檢查信號是否需要確認"""
        signal_type = new_signal.get('signal')
        confidence = new_signal.get('confidence', 0.0)
        
        # 高信心度信號直接確認
        if confidence >= 0.8:
            return True
        
        # 檢查是否有連續的同類型信號
        recent_signals = self._get_recent_signals(symbol, hours=2)
        same_type_count = sum(1 for s in recent_signals if s['signal'] == signal_type)
        
        # 需要至少2次相同信號才確認
        return same_type_count >= 1
    
    def _is_duplicate_signal(self, symbol: str, signal_type: str, confidence: float) -> bool:
        """檢查是否為重複信號"""
        recent_signals = self._get_recent_signals(symbol, hours=1)
        
        for signal in recent_signals:
            if (signal['signal'] == signal_type and 
                abs(signal['confidence'] - confidence) < 0.1):
                return True
        
        return False
    
    def _is_signal_reversal_reasonable(self, symbol: str, signal_type: str) -> bool:
        """檢查信號反轉是否合理"""
        recent_signals = self._get_recent_signals(symbol, hours=12)
        
        if len(recent_signals) < 2:
            return True
        
        # 檢查最近12小時內的信號反轉次數
        reversals = 0
        for i in range(1, len(recent_signals)):
            if recent_signals[i]['signal'] != recent_signals[i-1]['signal']:
                reversals += 1
        
        # 如果反轉次數過多，可能是雜訊
        if reversals >= 3:
            return False
        
        return True
    
    def _record_signal(self, symbol: str, signal: Dict, timestamp: datetime):
        """記錄信號到歷史"""
        signal_record = {
            'signal': signal.get('signal'),
            'confidence': signal.get('confidence'),
            'timestamp': timestamp.isoformat(),
            'reasons': signal.get('reasons', []),
            'strategy': signal.get('strategy')
        }
        
        if symbol not in self.signal_history:
            self.signal_history[symbol] = []
        
        self.signal_history[symbol].append(signal_record)
        
        # 保持最近100條記錄
        if len(self.signal_history[symbol]) > 100:
            self.signal_history[symbol] = self.signal_history[symbol][-100:]
        
        # 保存到文件
        self._save_signal_history()
    
    def get_signal_statistics(self, symbol: str, days: int = 7) -> Dict:
        """獲取信號統計信息"""
        recent_signals = self._get_recent_signals(symbol, hours=days*24)
        
        if not recent_signals:
            return {
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'hold_signals': 0,
                'avg_confidence': 0.0,
                'signal_frequency': 0.0
            }
        
        buy_count = sum(1 for s in recent_signals if s['signal'] == 'BUY')
        sell_count = sum(1 for s in recent_signals if s['signal'] == 'SELL')
        hold_count = sum(1 for s in recent_signals if s['signal'] == 'HOLD')
        
        avg_confidence = sum(s['confidence'] for s in recent_signals) / len(recent_signals)
        signal_frequency = len(recent_signals) / days  # 每天平均信號數
        
        return {
            'total_signals': len(recent_signals),
            'buy_signals': buy_count,
            'sell_signals': sell_count,
            'hold_signals': hold_count,
            'avg_confidence': avg_confidence,
            'signal_frequency': signal_frequency,
            'last_signal_time': recent_signals[-1]['timestamp'] if recent_signals else None
        }
    
    def clear_old_signals(self, days: int = 30):
        """清理舊的信號記錄"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        for symbol in self.signal_history:
            filtered_signals = []
            for signal in self.signal_history[symbol]:
                signal_time = datetime.fromisoformat(signal['timestamp'])
                if signal_time >= cutoff_time:
                    filtered_signals.append(signal)
            
            self.signal_history[symbol] = filtered_signals
        
        self._save_signal_history()
        print(f"已清理{days}天前的舊信號記錄")
    
    def get_filter_config(self) -> Dict:
        """獲取過濾器配置"""
        return {
            'cooldown_hours': self.cooldown_hours,
            'min_confidence_threshold': self.min_confidence_threshold,
            'signal_confirmation_required': self.signal_confirmation_required
        }
    
    def update_filter_config(self, **kwargs):
        """更新過濾器配置"""
        if 'cooldown_hours' in kwargs:
            self.cooldown_hours = kwargs['cooldown_hours']
        if 'min_confidence_threshold' in kwargs:
            self.min_confidence_threshold = kwargs['min_confidence_threshold']
        if 'signal_confirmation_required' in kwargs:
            self.signal_confirmation_required = kwargs['signal_confirmation_required']