"""Fetch service encapsulating proxy source aggregation and optional fast scan."""
from __future__ import annotations

from typing import List
import logging

from proxy_manager.models import ProxyNode

logger = logging.getLogger(__name__)


class FetchService:
    def __init__(self, manager: "ProxyManager") -> None:  # type: ignore
        self.manager = manager

    async def fetch_all(self) -> List[ProxyNode]:
        raw = await self.manager.fetcher_manager.fetch_all_proxies()
        adv = await self.manager.advanced_fetcher_manager.fetch_all_proxies()
        all_proxies = raw + adv
        logger.info(
            "📥 FetchService 聚合來源: 傳統=%d 高級=%d 總計=%d",
            len(raw), len(adv), len(all_proxies)
        )
        if not all_proxies:
            return []
        cfg = getattr(self.manager, "config", None)
        if cfg and getattr(cfg, "scanner", None) and getattr(cfg.scanner, "enable_fast_scan", False):
            logger.info("🔍 FetchService 執行快速端口掃描預篩選 ...")
            all_proxies = await self.manager.scanner.scan_proxy_list(all_proxies)
            logger.info("🎯 快速掃描後剩餘 %d 個代理", len(all_proxies))
        return all_proxies
