"""日誌工具模組

提供統一的日誌配置和獲取功能。
"""

import logging
import sys
from typing import Optional
from pathlib import Path


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> None:
    """設置日誌配置
    
    Args:
        level: 日誌級別
        log_file: 日誌文件路徑
        format_string: 日誌格式字符串
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 配置根日誌記錄器
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 如果指定了日誌文件，添加文件處理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(format_string))
        
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """獲取日誌記錄器
    
    Args:
        name: 日誌記錄器名稱
        
    Returns:
        日誌記錄器實例
    """
    return logging.getLogger(name)


# 默認設置日誌
setup_logging()