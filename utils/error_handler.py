"""
統一錯誤處理模塊
提供一致的錯誤處理機制和日誌記錄
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps
import json
import os

class StockMonitorError(Exception):
    """股票監控系統基礎異常類"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code or "GENERIC_ERROR"
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)

class DataFetchError(StockMonitorError):
    """數據獲取錯誤"""
    def __init__(self, symbol: str, message: str = "數據獲取失敗"):
        super().__init__(
            message=f"{symbol}: {message}",
            error_code="DATA_FETCH_ERROR",
            details={"symbol": symbol}
        )

class StrategyError(StockMonitorError):
    """策略計算錯誤"""
    def __init__(self, strategy: str, symbol: str, message: str = "策略計算失敗"):
        super().__init__(
            message=f"{strategy} 策略對 {symbol} 計算失敗: {message}",
            error_code="STRATEGY_ERROR",
            details={"strategy": strategy, "symbol": symbol}
        )

class APIError(StockMonitorError):
    """API調用錯誤"""
    def __init__(self, endpoint: str, message: str = "API調用失敗"):
        super().__init__(
            message=f"API {endpoint} 調用失敗: {message}",
            error_code="API_ERROR",
            details={"endpoint": endpoint}
        )

class ValidationError(StockMonitorError):
    """數據驗證錯誤"""
    def __init__(self, field: str, value: Any, message: str = "數據驗證失敗"):
        super().__init__(
            message=f"驗證失敗 [{field}={value}]: {message}",
            error_code="VALIDATION_ERROR",
            details={"field": field, "value": str(value)}
        )

class ErrorHandler:
    """統一錯誤處理器"""
    
    def __init__(self, log_file: str = "stock_monitor_errors.log"):
        self.log_file = log_file
        self.setup_logging()
        self.error_stats = {}
    
    def setup_logging(self):
        """設置日誌記錄"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('stock_monitor')
    
    def handle_error(self, error: Exception, context: Dict = None) -> Dict:
        """
        處理錯誤並返回標準化的錯誤響應
        
        Args:
            error: 異常對象
            context: 錯誤上下文信息
            
        Returns:
            Dict: 標準化錯誤響應
        """
        context = context or {}
        
        # 如果是自定義錯誤
        if isinstance(error, StockMonitorError):
            error_response = {
                'success': False,
                'error_code': error.error_code,
                'message': error.message,
                'details': error.details,
                'timestamp': error.timestamp,
                'context': context
            }
        else:
            # 處理其他異常
            error_response = {
                'success': False,
                'error_code': 'UNEXPECTED_ERROR',
                'message': str(error),
                'details': {
                    'error_type': type(error).__name__,
                    'traceback': traceback.format_exc()
                },
                'timestamp': datetime.now().isoformat(),
                'context': context
            }
        
        # 記錄錯誤
        self.log_error(error_response)
        
        # 更新錯誤統計
        self.update_error_stats(error_response['error_code'])
        
        return error_response
    
    def log_error(self, error_response: Dict):
        """記錄錯誤到日誌"""
        log_message = (
            f"[{error_response['error_code']}] "
            f"{error_response['message']} | "
            f"Context: {error_response.get('context', {})} | "
            f"Details: {error_response.get('details', {})}"
        )
        
        self.logger.error(log_message)
    
    def update_error_stats(self, error_code: str):
        """更新錯誤統計"""
        if error_code not in self.error_stats:
            self.error_stats[error_code] = {
                'count': 0,
                'first_occurrence': datetime.now().isoformat(),
                'last_occurrence': None
            }
        
        self.error_stats[error_code]['count'] += 1
        self.error_stats[error_code]['last_occurrence'] = datetime.now().isoformat()
    
    def get_error_stats(self) -> Dict:
        """獲取錯誤統計信息"""
        return self.error_stats.copy()
    
    def clear_error_stats(self):
        """清空錯誤統計"""
        self.error_stats.clear()

# 全局錯誤處理器實例
error_handler = ErrorHandler()

def handle_exceptions(error_context: str = None, 
                     default_return: Any = None,
                     re_raise: bool = False):
    """
    裝飾器：統一錯誤處理
    
    Args:
        error_context: 錯誤上下文描述
        default_return: 發生錯誤時的默認返回值
        re_raise: 是否重新拋出異常
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    'function': func.__name__,
                    'args': str(args)[:200],  # 限制長度
                    'kwargs': str(kwargs)[:200],
                    'context': error_context
                }
                
                error_response = error_handler.handle_error(e, context)
                
                if re_raise:
                    raise e
                
                return default_return if default_return is not None else error_response
        
        return wrapper
    return decorator

def handle_api_exceptions(func: Callable):
    """
    API專用錯誤處理裝飾器
    返回標準化的API錯誤響應
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = {
                'api_function': func.__name__,
                'endpoint': kwargs.get('endpoint', 'unknown'),
                'method': getattr(func, '__method__', 'unknown')
            }
            
            error_response = error_handler.handle_error(e, context)
            
            # API錯誤響應格式
            return {
                'success': False,
                'error': error_response['message'],
                'error_code': error_response['error_code'],
                'timestamp': error_response['timestamp'],
                'details': error_response.get('details', {})
            }
    
    return wrapper

def validate_data(data: Dict, required_fields: list, field_types: Dict = None) -> None:
    """
    數據驗證工具函數
    
    Args:
        data: 要驗證的數據
        required_fields: 必需欄位列表
        field_types: 欄位類型要求 {field: type}
        
    Raises:
        ValidationError: 驗證失敗時拋出
    """
    # 檢查必需欄位
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValidationError(field, None, f"必需欄位 {field} 缺失")
    
    # 檢查欄位類型
    if field_types:
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                raise ValidationError(
                    field, 
                    data[field], 
                    f"欄位類型錯誤，期望 {expected_type.__name__}，實際 {type(data[field]).__name__}"
                )

def safe_execute(func: Callable, default_value: Any = None, 
                context: str = None, **func_kwargs) -> Any:
    """
    安全執行函數，捕獲所有異常
    
    Args:
        func: 要執行的函數
        default_value: 異常時的默認返回值
        context: 執行上下文
        **func_kwargs: 函數參數
        
    Returns:
        函數結果或默認值
    """
    try:
        return func(**func_kwargs)
    except Exception as e:
        error_handler.handle_error(e, {'context': context, 'function': func.__name__})
        return default_value

# 常用的安全執行函數
def safe_get_price(analyzer, default: float = 0.0) -> float:
    """安全獲取股價"""
    return safe_execute(
        analyzer.get_current_price,
        default_value=default,
        context="獲取當前股價"
    ) or default

def safe_calculate_indicator(calc_func: Callable, default: Any = None, **kwargs) -> Any:
    """安全計算技術指標"""
    return safe_execute(
        calc_func,
        default_value=default,
        context="計算技術指標",
        **kwargs
    )

# 錯誤恢復工具
class ErrorRecovery:
    """錯誤恢復工具"""
    
    @staticmethod
    def retry_with_backoff(func: Callable, max_retries: int = 3, 
                          base_delay: float = 1.0, **func_kwargs):
        """
        帶退避的重試機制
        
        Args:
            func: 要重試的函數
            max_retries: 最大重試次數
            base_delay: 基礎延遲時間（秒）
            **func_kwargs: 函數參數
        """
        import time
        
        for attempt in range(max_retries + 1):
            try:
                return func(**func_kwargs)
            except Exception as e:
                if attempt == max_retries:
                    error_handler.handle_error(e, {
                        'function': func.__name__,
                        'attempt': attempt + 1,
                        'max_retries': max_retries
                    })
                    raise e
                
                delay = base_delay * (2 ** attempt)  # 指數退避
                time.sleep(delay)
    
    @staticmethod
    def fallback_chain(functions: list, context: str = None):
        """
        備用函數鏈，依次嘗試執行直到成功
        
        Args:
            functions: [(func, kwargs), ...] 函數和參數的列表
            context: 執行上下文
            
        Returns:
            第一個成功執行的函數結果
        """
        for i, (func, kwargs) in enumerate(functions):
            try:
                result = func(**kwargs)
                if i > 0:  # 使用了備用函數
                    error_handler.logger.info(f"使用備用函數 {func.__name__} 成功恢復")
                return result
            except Exception as e:
                if i == len(functions) - 1:  # 最後一個函數也失敗了
                    error_handler.handle_error(e, {
                        'context': context,
                        'fallback_chain_exhausted': True,
                        'attempted_functions': [f.__name__ for f, _ in functions]
                    })
                    raise e
                continue
        
        return None