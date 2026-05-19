"""Configuración común para tests."""
import os
import tempfile

import pytest


@pytest.fixture(scope="session", autouse=True)
def _test_env():
    """Cada sesión de tests usa una BD SQLite temporal y secret de prueba."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="komparo_test_")
    os.close(fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{path}"
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["ENVIRONMENT"] = "development"
    yield
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    """Cada test arranca con los contadores de rate limit a cero."""
    from api.rate_limit import reset
    reset()
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    with TestClient(app) as c:
        yield c


def register_and_login(client, email="user@test.com", password="testpass123", name="Test"):
    r = client.post(
        "/auth/register",
        json={"email": email, "password": password, "name": name},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, r.json()["user"]
