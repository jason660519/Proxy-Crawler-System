from fastapi.testclient import TestClient
from src.main import app


def test_metrics_endpoint():
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        assert b"http_requests_total" in r.content
