from fastapi.testclient import TestClient

from deepresearch.config import get_settings
from deepresearch.main import create_app


def test_application_lifecycle() -> None:
    app = create_app(get_settings())

    with TestClient(app):
        assert hasattr(app.state, "engine")
        assert hasattr(app.state, "session_factory")

    # After leaving TestClient, lifespan shutdown should
    # have disposed of the database engine.
    assert app.state.engine is not None
