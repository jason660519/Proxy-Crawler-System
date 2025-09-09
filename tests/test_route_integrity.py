"""Route integrity tests ensuring no duplicate paths+methods and core endpoints present."""
from fastapi.testclient import TestClient

from src.main import app

def test_no_duplicate_routes():
    seen = {}
    duplicates = []
    for route in app.routes:
        methods = getattr(route, 'methods', set()) or set()
        path = getattr(route, 'path', None)
        if not path:
            continue
        for m in methods:
            key = (m, path)
            if key in seen:
                duplicates.append(key)
            else:
                seen[key] = 1
    assert not duplicates, f"Duplicate route definitions found: {duplicates}"

def test_core_endpoints_exist():
    client = TestClient(app)
    # minimal smoke checks
    r = client.get('/api/health')
    assert r.status_code in (200, 401, 403)  # allow auth gating
    r2 = client.get('/api/stats')
    assert r2.status_code in (200, 401, 403)
    r3 = client.post('/api/proxies/fetch', json={})
    assert r3.status_code in (200, 401, 403)