from fastapi.testclient import TestClient

from claim360.api.main import app
from tests.conftest import requires_postgres

client = TestClient(app)


def test_health_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@requires_postgres
def test_ready_database() -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
