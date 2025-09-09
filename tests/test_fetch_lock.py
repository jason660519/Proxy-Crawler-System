import asyncio
import pytest
from src.proxy_manager.manager import ProxyManager, ProxyManagerConfig


@pytest.mark.asyncio
async def test_fetch_lock(monkeypatch):
    cfg = ProxyManagerConfig()
    cfg.auto_fetch_enabled = False
    manager = ProxyManager(cfg)
    await manager._initialize_components()

    calls = {"n": 0}

    async def fake_fetch_all():
        calls["n"] += 1
        await asyncio.sleep(0.05)
        return []

    async def fake_adv():
        await asyncio.sleep(0.01)
        return []

    monkeypatch.setattr(manager.fetcher_manager, "fetch_all_proxies", fake_fetch_all)
    monkeypatch.setattr(manager.advanced_fetcher_manager, "fetch_all_proxies", fake_adv)

    await asyncio.gather(*(manager.fetch_proxies() for _ in range(3)))
    assert calls["n"] == 3
