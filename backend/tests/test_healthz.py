from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "best-select backend",
        "version": "0.1.0",
        "status": "running",
    }


def test_healthz() -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_v1_healthz() -> None:
    response = client.get("/api/v1/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_runtime() -> None:
    response = client.get("/api/v1/runtime")

    assert response.status_code == 200
    assert response.json() == {
        "app_env": "dev",
        "app_version": "0.1.0",
        "supabase_enabled": False,
    }


def test_db_healthz_not_configured() -> None:
    response = client.get("/api/v1/db/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "not_configured",
        "configured": False,
    }
