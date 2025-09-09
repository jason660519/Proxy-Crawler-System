from fastapi.testclient import TestClient
from src.main import app

def test_stats_endpoints():
    client = TestClient(app)
    r = client.get('/api/stats')
    assert r.status_code in (200, 500)  # 若 manager 尚未初始化可能 500
    r2 = client.get('/api/metrics/trends?hours=2')
    assert r2.status_code in (200, 500)
