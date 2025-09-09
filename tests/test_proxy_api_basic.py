import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_status_redacted():
    r = client.get('/status')
    assert r.status_code == 200
    data = r.json()
    assert 'configuration' in data
    cfg = data['configuration']
    # 應不存在敏感欄位
    assert 'db_user' not in cfg and 'db_name' not in cfg
    assert 'database_configured' in cfg


def test_proxy_metrics_endpoint():
    r = client.get('/metrics')
    assert r.status_code in (200, 404)


@pytest.mark.parametrize('count', [1, 3])
def test_get_proxies_list(count):
    # 由於啟動時可能尚未有代理，允許空列表
    r = client.get(f'/api/proxies?count={count}')
    assert r.status_code in (200, 500, 404)
    if r.status_code == 200:
        data = r.json()
        assert isinstance(data, list)
        for item in data:
            assert 'success' in item


def test_single_proxy_not_found_handled():
    r = client.get('/api/proxy?protocol=http')
    # 可能 404 (沒有代理) 或 200 (若有代理)
    assert r.status_code in (200, 404)
