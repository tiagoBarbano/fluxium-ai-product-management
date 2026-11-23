from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_status_and_request_ids() -> None:
    client = TestClient(create_app())

    response = client.get(
        "/api/v1/health",
        headers={"Correlation-Id": "correlation-test", "Trace-Id": "trace-test"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "environment": "local"}
    assert response.headers["Correlation-Id"] == "correlation-test"
    assert response.headers["Trace-Id"] == "trace-test"


def test_cors_allows_local_frontend_preflight() -> None:
    client = TestClient(create_app())

    response = client.options(
        "/api/v1/identity/users/token",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
