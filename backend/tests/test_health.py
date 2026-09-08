import pytest
from sqlalchemy.exc import OperationalError

from app.core.db import get_db
from app.main import app


@pytest.mark.db  # DB 까지 확인한다
def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_health_reports_db_down(client):
    class Broken:
        def execute(self, *_):
            raise OperationalError("select 1", {}, Exception("connection refused"))

    def broken():
        yield Broken()

    app.dependency_overrides[get_db] = broken
    try:
        res = client.get("/health")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert res.status_code == 503
    assert res.json() == {"status": "db unreachable"}


def test_security_headers(client):
    h = client.get("/health").headers
    assert h["x-content-type-options"] == "nosniff"
    assert h["x-frame-options"] == "DENY"
    assert h["content-security-policy"] == "frame-ancestors 'none'"
    assert h["referrer-policy"] == "no-referrer"


@pytest.mark.db
def test_cors_header(client):
    r = client.get("/contents?size=1", headers={"Origin": "http://localhost:3000"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"
