from fastapi.testclient import TestClient

from src.api.main import app


def test_health():
    client = TestClient(app)
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_root():
    client = TestClient(app)
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data.get("app") == "Fiserv Payments Assistant"
    assert data.get("docs") == "/docs"
