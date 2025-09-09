#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核心日誌模組

此模組提供系統的核心日誌功能，包括：
- 日誌器設置和配置
- 結構化日誌記錄
- 日誌格式化
- 日誌輸出管理
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json


class StructuredFormatter(logging.Formatter):
    """結構化日誌格式器
    
    將日誌記錄格式化為結構化格式（JSON）。
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日誌記錄
        
        Args:
            record: 日誌記錄
        
        Returns:
            str: 格式化後的日誌字符串
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加異常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加額外的字段
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data, ensure_ascii=False)


class SimpleFormatter(logging.Formatter):
    """簡單日誌格式器
    
    提供易讀的日誌格式。
    """
    
    def __init__(self):
        """初始化格式器"""
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    structured: bool = False,
    console: bool = True
) -> logging.Logger:
    """設置日誌器
    
    Args:
        name: 日誌器名稱
        level: 日誌級別
        log_file: 日誌文件路徑
        structured: 是否使用結構化格式
        console: 是否輸出到控制台
    
    Returns:
        logging.Logger: 配置好的日誌器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除現有的處理器
    logger.handlers.clear()
    
    # 選擇格式器
    formatter = StructuredFormatter() if structured else SimpleFormatter()
    
    # 添加控制台處理器
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 添加文件處理器
    if log_file:
        # 確保日誌目錄存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """獲取日誌器
    
    Args:
        name: 日誌器名稱
    
    Returns:
        logging.Logger: 日誌器實例
    """
    return logging.getLogger(name)


class LoggerMixin:
    """日誌器混入類
    
    為類提供日誌記錄功能。
    """
    
    @property
    def logger(self) -> logging.Logger:
        """獲取日誌器
        
        Returns:
            logging.Logger: 日誌器實例
        """
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
    
    def log_info(self, message: str, **kwargs):
        """記錄信息日誌
        
        Args:
            message: 日誌消息
            **kwargs: 額外的日誌數據
        """
        self._log_with_extra(logging.INFO, message, kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """記錄警告日誌
        
        Args:
            message: 日誌消息
            **kwargs: 額外的日誌數據
        """
        self._log_with_extra(logging.WARNING, message, kwargs)
    
    def log_error(self, message: str, **kwargs):
        """記錄錯誤日誌
        
        Args:
            message: 日誌消息
            **kwargs: 額外的日誌數據
        """
        self._log_with_extra(logging.ERROR, message, kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """記錄調試日誌
        
        Args:
            message: 日誌消息
            **kwargs: 額外的日誌數據
        """
        self._log_with_extra(logging.DEBUG, message, kwargs)
    
    def _log_with_extra(self, level: int, message: str, extra_data: Dict[str, Any]):
        """記錄帶額外數據的日誌
        
        Args:
            level: 日誌級別
            message: 日誌消息
            extra_data: 額外數據
        """
        if extra_data:
            # 創建一個帶額外數據的日誌記錄
            record = self.logger.makeRecord(
                self.logger.name, level, "", 0, message, (), None
            )
            record.extra_data = extra_data
            self.logger.handle(record)
        else:
            self.logger.log(level, message)


# 默認日誌器設置
_default_logger: Optional[logging.Logger] = None


def get_default_logger() -> logging.Logger:
    """獲取默認日誌器
    
    Returns:
        logging.Logger: 默認日誌器
    """
    global _default_logger
    
    if _default_logger is None:
        _default_logger = setup_logger("proxy_crawler", level="INFO")
    
    return _default_logger


def configure_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    structured: bool = False
):
    """配置全局日誌設置
    
    Args:
        level: 日誌級別
        log_file: 日誌文件路徑
        structured: 是否使用結構化格式
    """
    global _default_logger
    
    # 重新設置默認日誌器
    _default_logger = setup_logger(
        "proxy_crawler",
        level=level,
        log_file=log_file,
        structured=structured
    )
    
    # 設置根日誌器級別
    logging.getLogger().setLevel(getattr(logging, level.upper()))