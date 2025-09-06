"""批量驗證器模組

此模組提供批量代理驗證功能。
"""

import asyncio
import logging
from typing import List, Optional, TYPE_CHECKING

from .proxy_validator import ProxyValidator, ValidationResult
from ..models import ProxyNode

if TYPE_CHECKING:
    from ..config import ValidationConfig

logger = logging.getLogger(__name__)


class BatchValidator:
    """批量驗證器（支持大規模驗證）"""
    
    def __init__(self, config: Optional['ValidationConfig'] = None, batch_size: int = 100):
        """初始化批量驗證器
        
        Args:
            config: 驗證配置
            batch_size: 批次大小
        """
        # 延遲導入以避免循環依賴
        if config is None:
            from ..config import ValidationConfig
            self.config = ValidationConfig()
        else:
            self.config = config
        self.batch_size = batch_size
        self.validator: Optional[ProxyValidator] = None
    
    async def validate_large_batch(self, proxies: List[ProxyNode]) -> List[ValidationResult]:
        """驗證大批量代理
        
        Args:
            proxies: 代理列表
            
        Returns:
            驗證結果列表
        """
        logger.info(f"🔍 開始大批量驗證 {len(proxies)} 個代理，批次大小: {self.batch_size}")
        
        all_results = []
        
        async with ProxyValidator(self.config) as validator:
            self.validator = validator
            
            # 分批處理
            for i in range(0, len(proxies), self.batch_size):
                batch = proxies[i:i + self.batch_size]
                logger.info(f"處理批次 {i//self.batch_size + 1}/{(len(proxies)-1)//self.batch_size + 1}")
                
                # 並發驗證當前批次
                tasks = [validator.validate(proxy) for proxy in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 處理結果
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"驗證過程中發生錯誤: {result}")
                        continue
                    all_results.append(result)
                
                # 批次間延遲
                if i + self.batch_size < len(proxies):
                    await asyncio.sleep(1)
        
        logger.info(f"✅ 大批量驗證完成，共處理 {len(all_results)} 個結果")
        return all_results
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if self.validator:
            await self.validator.__aexit__(exc_type, exc_val, exc_tb)