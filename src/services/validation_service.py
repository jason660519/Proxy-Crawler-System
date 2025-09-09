"""Validation service extracts batch validation & filtering logic."""
from __future__ import annotations

from typing import List
import logging
from proxy_manager.models import ProxyNode

logger = logging.getLogger(__name__)


class ValidationService:
    def __init__(self, manager: "ProxyManager") -> None:  # type: ignore
        self.manager = manager

    async def validate(self, proxies: List[ProxyNode]) -> List[ProxyNode]:
        if not proxies:
            return []
        if self.manager.batch_validator:
            results = await self.manager.batch_validator.validate_large_batch(proxies)
            valid = [r.proxy for r in results if r.is_working]
            logger.info("✅ ValidationService: %d/%d 可用", len(valid), len(proxies))
            return valid
        logger.warning("⚠️ ValidationService: 批量驗證器未初始化，跳過驗證")
        return proxies
