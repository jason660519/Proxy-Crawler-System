from fastapi.testclient import TestClient
from src.main import app

def test_get_proxy_response_structure():
    client = TestClient(app)
    r = client.get('/api/proxy')  # 可能 404 (空池)
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        data = r.json()
        assert 'success' in data and 'data' in data
