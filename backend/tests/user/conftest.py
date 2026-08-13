import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import settings

PASSWORD = "secret1234"


@pytest.fixture
def credentials():
    """실행마다 새 이메일
    테스트가 끝나면 계정을 지운다
    user_contents 는 FK CASCADE 로 함께 제거
    """
    payload = {
        "email": f"test-{uuid.uuid4().hex[:12]}@example.com",
        "password": PASSWORD,
        "nickname": "테스터",
    }
    yield payload

    with create_engine(settings.DIRECT_URL).begin() as conn:
        conn.execute(text("delete from users where email = :e"), {"e": payload["email"]})


@pytest.fixture
def auth_client(client: TestClient, credentials: dict) -> TestClient:
    """가입 + 로그인까지 된 클라이언트"""
    client.post("/auth/signup", json=credentials)
    client.post(
        "/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )
    return client
