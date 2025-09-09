#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日誌記錄模組

此模組提供完整的日誌記錄功能，包括：
- 結構化日誌記錄
- 多種輸出格式（JSON、文本、彩色輸出）
- 日誌輪轉和歸檔
- 性能監控日誌
- 錯誤追蹤和聚合
- 日誌分析和查詢
- 遠程日誌傳輸
"""

import logging
import logging.handlers
import json
import sys
import traceback
import threading
import queue
import time
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import gzip
import shutil
from collections import defaultdict, deque
import asyncio
from contextlib import contextmanager

# 第三方庫（如果可用）
try:
    import colorama
    from colorama import Fore, Back, Style
    colorama.init()
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    Fore = Back = Style = type('MockColor', (), {'__getattr__': lambda self, name: ''})()


class LogLevel(Enum):
    """日誌級別枚舉"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(Enum):
    """日誌格式枚舉"""
    TEXT = "text"
    JSON = "json"
    COLORED = "colored"
    STRUCTURED = "structured"


class LogDestination(Enum):
    """日誌目標枚舉"""
    CONSOLE = "console"
    FILE = "file"
    ROTATING_FILE = "rotating_file"
    SYSLOG = "syslog"
    REMOTE = "remote"
    MEMORY = "memory"


@dataclass
class LogEntry:
    """日誌條目數據類"""
    timestamp: datetime
    level: LogLevel
    logger_name: str
    message: str
    module: str
    function: str
    line_number: int
    thread_id: int
    process_id: int
    extra_data: Dict[str, Any] = field(default_factory=dict)
    exception_info: Optional[str] = None
    stack_trace: Optional[str] = None
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None


@dataclass
class LoggerConfig:
    """日誌器配置數據類"""
    name: str
    level: LogLevel = LogLevel.INFO
    format_type: LogFormat = LogFormat.TEXT
    destinations: List[LogDestination] = field(default_factory=lambda: [LogDestination.CONSOLE])
    
    # 文件配置
    log_file: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    # 格式配置
    date_format: str = "%Y-%m-%d %H:%M:%S"
    message_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 過濾配置
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    
    # 性能配置
    async_logging: bool = True
    buffer_size: int = 1000
    flush_interval: float = 1.0
    
    # 歸檔配置
    enable_compression: bool = True
    retention_days: int = 30


class ColoredFormatter(logging.Formatter):
    """彩色日誌格式化器"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE + Style.BRIGHT
    }
    
    def format(self, record):
        """格式化日誌記錄"""
        if not COLORAMA_AVAILABLE:
            return super().format(record)
        
        # 獲取顏色
        color = self.COLORS.get(record.levelname, '')
        reset = Style.RESET_ALL
        
        # 格式化消息
        formatted = super().format(record)
        
        # 應用顏色
        if color:
            formatted = f"{color}{formatted}{reset}"
        
        return formatted


class JSONFormatter(logging.Formatter):
    """JSON日誌格式化器"""
    
    def format(self, record):
        """格式化為JSON格式"""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread_id': record.thread,
            'process_id': record.process
        }
        
        # 添加異常信息
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # 添加額外數據
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)


class StructuredFormatter(logging.Formatter):
    """結構化日誌格式化器"""
    
    def format(self, record):
        """格式化為結構化格式"""
        # 基本信息
        parts = [
            f"[{datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')}]",
            f"[{record.levelname}]",
            f"[{record.name}]",
            f"[{record.module}:{record.funcName}:{record.lineno}]",
            record.getMessage()
        ]
        
        # 添加額外數據
        if hasattr(record, 'extra_data') and record.extra_data:
            extra_parts = [f"{k}={v}" for k, v in record.extra_data.items()]
            parts.append(f"[{', '.join(extra_parts)}]")
        
        # 添加異常信息
        if record.exc_info:
            parts.append(f"\nException: {self.formatException(record.exc_info)}")
        
        return " ".join(parts)


class AsyncLogHandler(logging.Handler):
    """異步日誌處理器"""
    
    def __init__(self, target_handler: logging.Handler, buffer_size: int = 1000, flush_interval: float = 1.0):
        """初始化異步日誌處理器
        
        Args:
            target_handler: 目標處理器
            buffer_size: 緩衝區大小
            flush_interval: 刷新間隔（秒）
        """
        super().__init__()
        self.target_handler = target_handler
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        
        # 日誌隊列
        self.log_queue = queue.Queue(maxsize=buffer_size)
        
        # 工作線程
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        
        # 控制標誌
        self.shutdown_flag = threading.Event()
    
    def emit(self, record):
        """發送日誌記錄"""
        try:
            self.log_queue.put_nowait(record)
        except queue.Full:
            # 隊列滿時丟棄最舊的記錄
            try:
                self.log_queue.get_nowait()
                self.log_queue.put_nowait(record)
            except queue.Empty:
                pass
    
    def _worker(self):
        """工作線程"""
        while not self.shutdown_flag.is_set():
            try:
                # 批量處理日誌
                records = []
                
                # 收集記錄
                try:
                    # 等待第一個記錄
                    record = self.log_queue.get(timeout=self.flush_interval)
                    records.append(record)
                    
                    # 收集更多記錄（非阻塞）
                    while len(records) < 100:  # 批量大小限制
                        try:
                            record = self.log_queue.get_nowait()
                            records.append(record)
                        except queue.Empty:
                            break
                
                except queue.Empty:
                    continue
                
                # 處理記錄
                for record in records:
                    try:
                        self.target_handler.emit(record)
                    except Exception as e:
                        # 避免日誌處理錯誤導致無限循環
                        print(f"日誌處理錯誤: {e}", file=sys.stderr)
                
                # 刷新目標處理器
                if hasattr(self.target_handler, 'flush'):
                    self.target_handler.flush()
                    
            except Exception as e:
                print(f"異步日誌工作線程錯誤: {e}", file=sys.stderr)
    
    def close(self):
        """關閉處理器"""
        self.shutdown_flag.set()
        
        # 處理剩餘的日誌
        while not self.log_queue.empty():
            try:
                record = self.log_queue.get_nowait()
                self.target_handler.emit(record)
            except queue.Empty:
                break
            except Exception as e:
                print(f"關閉時處理日誌錯誤: {e}", file=sys.stderr)
        
        # 關閉目標處理器
        self.target_handler.close()
        
        # 等待工作線程結束
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        
        super().close()


class LogAnalyzer:
    """日誌分析器
    
    提供日誌分析和統計功能。
    """
    
    def __init__(self, retention_hours: int = 24):
        """初始化日誌分析器
        
        Args:
            retention_hours: 數據保留時間（小時）
        """
        self.retention_hours = retention_hours
        
        # 統計數據
        self.log_counts: Dict[str, int] = defaultdict(int)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.recent_logs: deque = deque(maxlen=10000)
        self.error_patterns: Dict[str, int] = defaultdict(int)
        
        # 性能統計
        self.response_times: deque = deque(maxlen=1000)
        self.request_counts: Dict[str, int] = defaultdict(int)
        
        # 清理任務
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def add_log_entry(self, entry: LogEntry) -> None:
        """添加日誌條目"""
        # 更新統計
        self.log_counts[entry.level.value] += 1
        self.recent_logs.append(entry)
        
        # 錯誤分析
        if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self.error_counts[entry.module] += 1
            
            # 提取錯誤模式
            if entry.exception_info:
                error_type = entry.exception_info.split(':')[0] if ':' in entry.exception_info else entry.exception_info
                self.error_patterns[error_type] += 1
        
        # 性能分析
        if 'response_time' in entry.extra_data:
            self.response_times.append(entry.extra_data['response_time'])
        
        if 'endpoint' in entry.extra_data:
            self.request_counts[entry.extra_data['endpoint']] += 1
    
    def get_statistics(self, hours: int = 1) -> Dict[str, Any]:
        """獲取統計信息"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 過濾最近的日誌
        recent_entries = [
            entry for entry in self.recent_logs 
            if entry.timestamp >= cutoff_time
        ]
        
        # 計算統計
        level_counts = defaultdict(int)
        module_counts = defaultdict(int)
        error_types = defaultdict(int)
        
        for entry in recent_entries:
            level_counts[entry.level.value] += 1
            module_counts[entry.module] += 1
            
            if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL] and entry.exception_info:
                error_type = entry.exception_info.split(':')[0] if ':' in entry.exception_info else 'Unknown'
                error_types[error_type] += 1
        
        # 性能統計
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            'time_range_hours': hours,
            'total_logs': len(recent_entries),
            'log_levels': dict(level_counts),
            'modules': dict(module_counts),
            'error_types': dict(error_types),
            'avg_response_time': avg_response_time,
            'top_endpoints': dict(sorted(self.request_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'error_rate': level_counts.get('ERROR', 0) / max(len(recent_entries), 1)
        }
    
    def search_logs(self, query: str, level: Optional[LogLevel] = None, hours: int = 24) -> List[LogEntry]:
        """搜索日誌"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        results = []
        for entry in self.recent_logs:
            if entry.timestamp < cutoff_time:
                continue
            
            if level and entry.level != level:
                continue
            
            if query.lower() in entry.message.lower():
                results.append(entry)
        
        return results
    
    async def start_cleanup_task(self) -> None:
        """啟動清理任務"""
        if self._cleanup_task:
            return
        
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_task(self) -> None:
        """停止清理任務"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _cleanup_loop(self) -> None:
        """清理循環"""
        while True:
            try:
                await asyncio.sleep(3600)  # 每小時清理一次
                self._cleanup_old_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"日誌清理錯誤: {e}", file=sys.stderr)
    
    def _cleanup_old_data(self) -> None:
        """清理舊數據"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        # 清理recent_logs中的舊數據
        while self.recent_logs and self.recent_logs[0].timestamp < cutoff_time:
            self.recent_logs.popleft()


class EnhancedLogger:
    """增強日誌器
    
    提供完整的日誌記錄功能。
    """
    
    def __init__(self, config: LoggerConfig):
        """初始化增強日誌器
        
        Args:
            config: 日誌器配置
        """
        self.config = config
        self.logger = logging.getLogger(config.name)
        self.logger.setLevel(getattr(logging, config.level.value))
        
        # 清除現有處理器
        self.logger.handlers.clear()
        
        # 日誌分析器
        self.analyzer = LogAnalyzer()
        
        # 設置處理器
        self._setup_handlers()
        
        # 上下文數據
        self._context_data = threading.local()
    
    def _setup_handlers(self) -> None:
        """設置日誌處理器"""
        for destination in self.config.destinations:
            handler = self._create_handler(destination)
            if handler:
                formatter = self._create_formatter()
                handler.setFormatter(formatter)
                
                # 異步處理
                if self.config.async_logging and destination != LogDestination.CONSOLE:
                    handler = AsyncLogHandler(
                        handler, 
                        self.config.buffer_size, 
                        self.config.flush_interval
                    )
                
                self.logger.addHandler(handler)
    
    def _create_handler(self, destination: LogDestination) -> Optional[logging.Handler]:
        """創建日誌處理器"""
        if destination == LogDestination.CONSOLE:
            return logging.StreamHandler(sys.stdout)
        
        elif destination == LogDestination.FILE:
            if self.config.log_file:
                log_path = Path(self.config.log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                return logging.FileHandler(log_path, encoding='utf-8')
        
        elif destination == LogDestination.ROTATING_FILE:
            if self.config.log_file:
                log_path = Path(self.config.log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                return logging.handlers.RotatingFileHandler(
                    log_path,
                    maxBytes=self.config.max_file_size,
                    backupCount=self.config.backup_count,
                    encoding='utf-8'
                )
        
        elif destination == LogDestination.SYSLOG:
            try:
                return logging.handlers.SysLogHandler()
            except Exception:
                return None
        
        return None
    
    def _create_formatter(self) -> logging.Formatter:
        """創建格式化器"""
        if self.config.format_type == LogFormat.JSON:
            return JSONFormatter()
        elif self.config.format_type == LogFormat.COLORED:
            return ColoredFormatter(self.config.message_format, self.config.date_format)
        elif self.config.format_type == LogFormat.STRUCTURED:
            return StructuredFormatter()
        else:
            return logging.Formatter(self.config.message_format, self.config.date_format)
    
    @contextmanager
    def context(self, **kwargs):
        """日誌上下文管理器"""
        # 保存舊的上下文
        old_context = getattr(self._context_data, 'context', {})
        
        # 設置新的上下文
        new_context = {**old_context, **kwargs}
        self._context_data.context = new_context
        
        try:
            yield
        finally:
            # 恢復舊的上下文
            self._context_data.context = old_context
    
    def _get_context_data(self) -> Dict[str, Any]:
        """獲取上下文數據"""
        return getattr(self._context_data, 'context', {})
    
    def _log(self, level: LogLevel, message: str, **kwargs) -> None:
        """內部日誌方法"""
        # 合併上下文數據
        extra_data = {**self._get_context_data(), **kwargs}
        
        # 創建日誌記錄
        record = self.logger.makeRecord(
            name=self.logger.name,
            level=getattr(logging, level.value),
            fn='',
            lno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        
        # 添加額外數據
        record.extra_data = extra_data
        
        # 發送日誌
        self.logger.handle(record)
        
        # 添加到分析器
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created),
            level=level,
            logger_name=record.name,
            message=message,
            module=record.module or 'unknown',
            function=record.funcName or 'unknown',
            line_number=record.lineno,
            thread_id=record.thread,
            process_id=record.process,
            extra_data=extra_data
        )
        
        self.analyzer.add_log_entry(log_entry)
    
    def debug(self, message: str, **kwargs) -> None:
        """記錄調試日誌"""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """記錄信息日誌"""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """記錄警告日誌"""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """記錄錯誤日誌"""
        if exception:
            kwargs['exception_info'] = str(exception)
            kwargs['stack_trace'] = traceback.format_exc()
        
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """記錄嚴重錯誤日誌"""
        if exception:
            kwargs['exception_info'] = str(exception)
            kwargs['stack_trace'] = traceback.format_exc()
        
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def get_statistics(self, hours: int = 1) -> Dict[str, Any]:
        """獲取日誌統計"""
        return self.analyzer.get_statistics(hours)
    
    def search_logs(self, query: str, level: Optional[LogLevel] = None, hours: int = 24) -> List[LogEntry]:
        """搜索日誌"""
        return self.analyzer.search_logs(query, level, hours)


class LoggerManager:
    """日誌器管理器
    
    管理多個日誌器實例。
    """
    
    def __init__(self):
        """初始化日誌器管理器"""
        self.loggers: Dict[str, EnhancedLogger] = {}
        self.default_config = LoggerConfig(
            name="default",
            level=LogLevel.INFO,
            format_type=LogFormat.STRUCTURED,
            destinations=[LogDestination.CONSOLE, LogDestination.ROTATING_FILE],
            log_file="logs/application.log"
        )
    
    def get_logger(self, name: str, config: Optional[LoggerConfig] = None) -> EnhancedLogger:
        """獲取日誌器"""
        if name not in self.loggers:
            if config is None:
                config = LoggerConfig(
                    name=name,
                    level=self.default_config.level,
                    format_type=self.default_config.format_type,
                    destinations=self.default_config.destinations,
                    log_file=f"logs/{name}.log" if self.default_config.log_file else None
                )
            
            self.loggers[name] = EnhancedLogger(config)
        
        return self.loggers[name]
    
    def configure_default(self, config: LoggerConfig) -> None:
        """配置默認設置"""
        self.default_config = config
    
    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有日誌器的統計信息"""
        return {
            name: logger.get_statistics() 
            for name, logger in self.loggers.items()
        }


# 全局日誌器管理器
logger_manager = LoggerManager()


def get_logger(name: str, config: Optional[LoggerConfig] = None) -> EnhancedLogger:
    """獲取日誌器的便捷函數"""
    return logger_manager.get_logger(name, config)


# 測試函數
async def main():
    """測試日誌記錄功能"""
    # 創建日誌器配置
    config = LoggerConfig(
        name="test_logger",
        level=LogLevel.DEBUG,
        format_type=LogFormat.COLORED,
        destinations=[LogDestination.CONSOLE, LogDestination.ROTATING_FILE],
        log_file="logs/test.log",
        async_logging=True
    )
    
    # 獲取日誌器
    logger = get_logger("test_logger", config)
    
    # 測試不同級別的日誌
    logger.info("應用程式啟動", component="main", version="1.0.0")
    logger.debug("調試信息", user_id="12345", action="login")
    logger.warning("警告信息", resource="memory", usage=85.5)
    
    # 測試上下文
    with logger.context(request_id="req-123", user_id="user-456"):
        logger.info("處理請求", endpoint="/api/users")
        logger.error("處理失敗", error_code="E001")
    
    # 測試異常日誌
    try:
        raise ValueError("測試異常")
    except Exception as e:
        logger.error("捕獲異常", exception=e)
    
    # 等待異步處理完成
    await asyncio.sleep(2)
    
    # 獲取統計信息
    stats = logger.get_statistics()
    print(f"日誌統計: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    
    # 搜索日誌
    results = logger.search_logs("請求")
    print(f"搜索結果: {len(results)} 條")


if __name__ == "__main__":
    asyncio.run(main())