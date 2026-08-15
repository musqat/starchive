import pytest
from sqlalchemy import create_engine, text

from app.core.config import settings


@pytest.mark.db  # 비밀번호 변경 → 새 비밀번호로 로그인됨
def test_change_password(auth_client, credentials):
    r = auth_client.patch(
        "/auth/password",
        json={"current_password": credentials["password"], "new_password": "newsecret1234"},
    )
    assert r.status_code == 204

    auth_client.post("/auth/logout")
    old = auth_client.post(
        "/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )
    assert old.status_code == 401

    new = auth_client.post(
        "/auth/login",
        json={"email": credentials["email"], "password": "newsecret1234"},
    )
    assert new.status_code == 200


@pytest.mark.db  # 현재 비밀번호가 틀리면 403
def test_change_password_wrong_current(auth_client):
    r = auth_client.patch(
        "/auth/password",
        json={"current_password": "wrongpassword", "new_password": "newsecret1234"},
    )
    assert r.status_code == 403


@pytest.mark.db  # 새 비밀번호가 8자 미만이면 422
def test_change_password_too_short(auth_client, credentials):
    r = auth_client.patch(
        "/auth/password",
        json={"current_password": credentials["password"], "new_password": "short"},
    )
    assert r.status_code == 422


@pytest.mark.db  # 탈퇴하면 기록도 사라지고 다시 로그인되지 않음
def test_withdraw(auth_client, credentials):
    auth_client.put("/me/records/tmdb_157336", json={"status": "DONE"})

    r = auth_client.post("/auth/withdraw", json={"password": credentials["password"]})
    assert r.status_code == 204

    again = auth_client.post(
        "/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )
    assert again.status_code == 401


@pytest.mark.db  # 비밀번호가 틀리면 탈퇴되지 않음
def test_withdraw_wrong_password(auth_client):
    r = auth_client.post("/auth/withdraw", json={"password": "wrongpassword"})
    assert r.status_code == 403

    assert auth_client.get("/auth/me").status_code == 200


@pytest.mark.db  # 비로그인 → 401
def test_requires_login(client):
    assert client.post("/auth/withdraw", json={"password": "x"}).status_code == 401
    assert (
        client.patch(
            "/auth/password", json={"current_password": "x", "new_password": "y" * 8}
        ).status_code
        == 401
    )


@pytest.mark.db  # 시드 계정은 로그인할 수 없다
def test_seed_cannot_log_in(client):
    """세단계 블로킹
    1. EmailStr 이 .invalid(예약 TLD) 를 주소 형식 단계에서 거부 → 422
    2. 조회에 is_seed = false 필터
    3. 비밀번호 해시로 임의 값
    """
    r = client.post(
        "/auth/login",
        json={"email": "seed-1@movielens.invalid", "password": "probe12345"},
    )

    assert r.status_code != 200
    assert "access_token" not in r.cookies


@pytest.mark.db  # is_seed 필터 자체를 확인한다
def test_seed_filter_excludes_from_login(client, credentials):
    """
    2단계 필터링
    - is_seed 면 로그인되지 않는다
    - 실제 시드는 .invalid 라 EmailStr 에서 먼저 막히므로, 필터가 도는지 따로 확인
    """
    client.post("/auth/signup", json=credentials)

    with create_engine(settings.DIRECT_URL).begin() as conn:
        conn.execute(
            text("update users set is_seed = true where email = :e"),
            {"e": credentials["email"]},
        )

    r = client.post(
        "/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )
    assert r.status_code == 401
