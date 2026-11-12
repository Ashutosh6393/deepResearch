from fastapi.testclient import TestClient

from deepresearch.config import get_settings
from deepresearch.exceptions import ResourceNotFoundError
from deepresearch.main import create_app


def test_application_error_handler() -> None:
    app = create_app(get_settings())

    @app.get("/test/not-found")
    async def not_found() -> None:
        raise ResourceNotFoundError("Research task not found")

    with TestClient(app) as client:
        response = client.get("/test/not-found")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "RESOURCE_NOT_FOUND",
            "message": "Research task not found",
        }
    }


def test_validation_error_handler() -> None:
    app = create_app(get_settings())

    @app.get("/test/validation")
    async def validation_endpoint(limit: int) -> dict[str, int]:
        return {"limit": limit}

    with TestClient(app) as client:
        response = client.get("/test/validation?limit=invalid")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_unexpected_error_handler() -> None:
    app = create_app(get_settings())

    @app.get("/test/unexpected")
    async def unexpected_error() -> None:
        raise RuntimeError("Internal database credentials")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/test/unexpected")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred.",
        }
    }

    assert "credentials" not in response.text
