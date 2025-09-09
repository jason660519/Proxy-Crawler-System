"""Persistence service for saving & rotating proxy pool data."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PersistenceService:
    def __init__(self, manager: "ProxyManager") -> None:  # type: ignore
        self.manager = manager

    async def save_snapshot(self) -> None:
        cfg = self.manager.config
        data_file = cfg.data_dir / "proxy_pools.json"
        await self.manager.pool_manager.save_to_file(data_file)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = cfg.backup_dir / f"proxy_pools_{timestamp}.json"
        await self.manager.pool_manager.save_to_file(backup_file)
        await self._prune_old(cfg.backup_dir, keep=10)
        logger.debug("PersistenceService: 已保存快照與備份 -> %s", backup_file)

    async def _prune_old(self, folder: Path, keep: int = 10) -> None:
        try:
            backups = sorted(folder.glob("proxy_pools_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            for old in backups[keep:]:
                try:
                    old.unlink()
                except Exception:
                    continue
        except Exception as e:  # pragma: no cover
            logger.warning("PersistenceService: 清理備份失敗 %s", e)
