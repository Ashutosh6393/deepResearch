from fastapi.testclient import TestClient

from deepresearch.config import get_settings
from deepresearch.main import create_app


def test_request_id_is_generated() -> None:
    app = create_app(get_settings())

    with TestClient(app) as client:
        response = client.get("/health/live")

    request_id = response.headers.get("X-Request-ID")

    assert response.status_code == 200
    assert request_id is not None
    assert len(request_id) == 36


def test_valid_incoming_request_id_is_preserved() -> None:
    app = create_app(get_settings())
    expected_request_id = "research-request-123"

    with TestClient(app) as client:
        response = client.get(
            "/health/live",
            headers={"X-Request-ID": expected_request_id},
        )

    assert response.headers["X-Request-ID"] == expected_request_id


def test_invalid_incoming_request_id_is_replaced() -> None:
    app = create_app(get_settings())

    with TestClient(app) as client:
        response = client.get(
            "/health/live",
            headers={"X-Request-ID": "invalid request id"},
        )

    request_id = response.headers["X-Request-ID"]

    assert request_id != "invalid request id"
    assert len(request_id) == 36


def test_request_id_is_returned_for_not_found_routes() -> None:
    app = create_app(get_settings())

    with TestClient(app) as client:
        response = client.get("/route-that-does-not-exist")

    assert response.status_code == 404
    assert response.headers.get("X-Request-ID") is not None





def test_request_id_is_present_on_unexpected_error() -> None:
    app = create_app(get_settings())

    @app.get("/test/unexpected-error")
    async def unexpected_error() -> None:
        raise RuntimeError("Internal failure")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/test/unexpected-error")

    assert response.status_code == 500
    assert response.headers.get("X-Request-ID") is not None


def test_invalid_request_id_is_replaced() -> None:
    app = create_app(get_settings())

    with TestClient(app) as client:
        response = client.get(
            "/health/live",
            headers={"X-Request-ID": "invalid request id"},
        )

    assert response.headers["X-Request-ID"] != "invalid request id"
