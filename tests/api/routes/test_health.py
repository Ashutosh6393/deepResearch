
from fastapi.testclient import TestClient

from deepresearch.config import get_settings
from deepresearch.main import create_app


def test_liveness_check() -> None:
    app = create_app(get_settings())

    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check() -> None:
    app = create_app(get_settings())

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
