import pytest


@pytest.mark.db  # 가입 → 201
def test_signup(client, credentials):
    r = client.post("/auth/signup", json=credentials)

    assert r.status_code == 201
    body = r.json()
    assert body["email"] == credentials["email"]
    assert body["nickname"] == credentials["nickname"]
    assert "password_hash" not in body  # UserOut 이 걸러야 함


@pytest.mark.db  # 같은 이메일 두 번 → 409
def test_signup_duplicate_email(client, credentials):
    client.post("/auth/signup", json=credentials)
    r = client.post("/auth/signup", json=credentials)
    assert r.status_code == 409
    assert r.json() == {"detail": "Email already registered"}


@pytest.mark.db  # 바이트 테스트 73+ → 422
@pytest.mark.parametrize("password", ["a" * 73, "é" * 40])  # é 는 2바이트라 40자 = 80바이트
def test_signup_password_over_bcrypt_limit(client, credentials, password):
    r = client.post("/auth/signup", json={**credentials, "password": password})
    assert r.status_code == 422


@pytest.mark.db  # 바이트 테스트 72 → 통과
def test_signup_password_at_bcrypt_limit(client, credentials):
    r = client.post("/auth/signup", json={**credentials, "password": "a" * 72})
    assert r.status_code == 201


@pytest.mark.db  # 로그인은 길이 제한이 없다. 틀린 비밀번호로 처리돼 401
def test_login_password_over_bcrypt_limit(client, credentials):
    client.post("/auth/signup", json=credentials)
    r = client.post("/auth/login", json={"email": credentials["email"], "password": "a" * 100})
    assert r.status_code == 401


@pytest.mark.db  # 로그인 → 200, 쿠키 설정
def test_login(client, credentials):
    client.post("/auth/signup", json=credentials)
    r = client.post(
        "/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )
    assert r.status_code == 200
    assert "access_token" in client.cookies


@pytest.mark.db  # 비밀번호 틀림 → 401
def test_login_wrong_password(client, credentials):
    client.post("/auth/signup", json=credentials)
    r = client.post("/auth/login", json={"email": credentials["email"], "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.db  # 없는 이메일 → 401. 위와 같은 응답
def test_login_unknown_email(client):
    r = client.post("/auth/login", json={"email": "nobody@example.com", "password": "password"})
    assert r.status_code == 401


@pytest.mark.db  # 실패가 쌓이면 잠기고, 잠긴 뒤에는 맞는 비밀번호도 막힌다
def test_login_lockout(client, credentials):
    from app.core.config import settings

    client.post("/auth/signup", json=credentials)
    wrong = {"email": credentials["email"], "password": "wrongwrong"}

    for _ in range(settings.MAX_FAILED_LOGINS):
        assert client.post("/auth/login", json=wrong).status_code == 401

    r = client.post("/auth/login", json=wrong)
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) > 0

    # 잠금은 비밀번호가 맞아도 풀리지 않는다
    correct = {"email": credentials["email"], "password": credentials["password"]}
    assert client.post("/auth/login", json=correct).status_code == 429


@pytest.mark.db  # 로그인에 성공하면 실패 기록이 지워진다
def test_successful_login_clears_failures(client, credentials, db_session):
    from sqlalchemy import select

    from app.domains.user.models import User

    client.post("/auth/signup", json=credentials)
    client.post("/auth/login", json={"email": credentials["email"], "password": "wrongwrong"})
    client.post(
        "/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )

    user = db_session.scalar(select(User).where(User.email == credentials["email"]))
    assert user.failed_logins == 0
    assert user.locked_until is None


@pytest.mark.db  # 비밀번호를 바꾸면 다른 기기의 토큰이 끊긴다
def test_password_change_invalidates_other_sessions(client, credentials):
    from fastapi.testclient import TestClient

    from app.main import app

    client.post("/auth/signup", json=credentials)
    login = {"email": credentials["email"], "password": credentials["password"]}
    client.post("/auth/login", json=login)

    # 다른 기기. 같은 계정으로 따로 로그인해 토큰을 하나 더 받는다
    other = TestClient(app)
    other.post("/auth/login", json=login)
    assert other.get("/auth/me").status_code == 200

    client.patch(
        "/auth/password",
        json={"current_password": credentials["password"], "new_password": "newsecret1234"},
    )

    assert other.get("/auth/me").status_code == 401  # 옛 토큰
    assert client.get("/auth/me").status_code == 200  # 바꾼 기기는 유지


@pytest.mark.db  # 비로그인 → 401
def test_me_requires_login(client):
    r = client.get("/auth/me")
    assert r.status_code == 401
    assert r.json() == {"detail": "not authorized"}


@pytest.mark.db  # 로그인 상태 → 200
def test_me(auth_client, credentials):
    assert auth_client.get("/auth/me").status_code == 200


@pytest.mark.db  # 로그아웃 → 204, 이후 401
def test_logout(auth_client):
    assert auth_client.get("/auth/me").status_code == 200  # 로그인 상태 확인
    assert auth_client.post("/auth/logout").status_code == 204
    assert auth_client.get("/auth/me").status_code == 401  # 쿠키 사라짐


# ---- Bearer 헤더 (앱) ----
# 앱용 로그인 API 는 2단계에서 만든다. 여기서는 app.core.security 의
# create_access_token(가입 응답의 id) 로 토큰을 직접 만든다.

def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.db  # 헤더 토큰으로도 로그인 상태가 된다
def test_me_with_bearer_header(client, credentials):
    from app.core.security import create_access_token

    user_id = client.post("/auth/signup", json=credentials).json()["id"]
    token = create_access_token(user_id)

    # 가입만 해서 쿠키가 없다. 헤더만으로 들어가는지 본다
    assert "access_token" not in client.cookies
    r = client.get("/auth/me", headers=_bearer(token))

    assert r.status_code == 200
    assert r.json()["email"] == credentials["email"]


@pytest.mark.db  # 서명이 틀린 토큰 → 401
def test_bearer_tampered_token(client, credentials):
    from app.core.security import create_access_token

    user_id = client.post("/auth/signup", json=credentials).json()["id"]
    token = create_access_token(user_id)
    header, payload, signature = token.split(".")
    first = "B" if signature[0] == "A" else "A"
    tampered = f"{header}.{payload}.{first}{signature[1:]}"
    
    assert "access_token" not in client.cookies
    r = client.get("/auth/me", headers=_bearer(tampered))

    assert r.status_code == 401
    assert r.json() == {"detail": "not authorized"}


@pytest.mark.db  # Bearer 가 아닌 방식 → 401
def test_bearer_wrong_scheme(client, credentials):
    from app.core.security import create_access_token

    user_id = client.post("/auth/signup", json=credentials).json()["id"]
    token = create_access_token(user_id)

    assert "access_token" not in client.cookies
    r = client.get("/auth/me", headers={"Authorization": f"Basic {token}"})

    assert r.status_code == 401
    assert r.json() == {"detail": "not authorized"}


@pytest.mark.db  # 헤더가 틀리면 쿠키가 맞아도 쿠키로 넘어가지 않는다
def test_bad_bearer_does_not_fall_back_to_cookie(auth_client):
    assert auth_client.get("/auth/me").status_code == 200   # 쿠키로 로그인된 상태
    r = auth_client.get("/auth/me", headers=_bearer("garbage"))
    assert r.status_code == 401


@pytest.mark.db  # 비밀번호를 바꾸면 옛 헤더 토큰도 끊긴다
def test_password_change_invalidates_bearer_token(client, credentials):
    from app.core.security import create_access_token

    user_id = client.post("/auth/signup", json=credentials).json()["id"]
    token = create_access_token(user_id)

    assert "access_token" not in client.cookies
    r = client.patch(
        "/auth/password",
        json={"current_password": credentials["password"], "new_password": "newsecret1234"},
        headers=_bearer(token),
    )
    assert r.status_code == 204

    r = client.get("/auth/me", headers=_bearer(token))
    assert r.status_code == 401
    assert r.json() == {"detail": "not authorized"}


# ---- POST /auth/token (앱 로그인) ----


def _login_body(credentials: dict) -> dict[str, str]:
    return {"email": credentials["email"], "password": credentials["password"]}


@pytest.mark.db  # 성공하면 토큰을 본문으로 주고 쿠키는 안 만든다
def test_token_returns_body_without_cookie(client, credentials):
    client.post("/auth/signup", json=credentials)

    r = client.post("/auth/token", json=_login_body(credentials))

    assert r.status_code == 200
    body = r.json()
    assert body["access_token"]  # 빈 문자열이 아니다
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == credentials["email"]
    assert "access_token" not in client.cookies  # 앱용이라 쿠키는 안 쓴다


@pytest.mark.db  # 받은 토큰으로 헤더 로그인이 된다
def test_token_works_as_bearer(client, credentials):
    client.post("/auth/signup", json=credentials)

    token = client.post("/auth/token", json=_login_body(credentials)).json()["access_token"]
    r = client.get("/auth/me", headers=_bearer(token))

    assert r.status_code == 200


@pytest.mark.db  # 틀린 비밀번호 → 401
def test_token_wrong_password(client, credentials):
    client.post("/auth/signup", json=credentials)

    token = client.post("/auth/token", json=_login_body(credentials)).json()["access_token"]
    r = client.get("/auth/me", headers=_bearer(token))

    client.post("/auth/signup", json=credentials)
    r = client.post("/auth/token", json={**_login_body(credentials), "password": "wrongwrong"})
    assert r.status_code == 401


@pytest.mark.db  # 실패가 쌓이면 /auth/token 도 잠긴다
def test_token_lockout(client, credentials):
    from app.core.config import settings

    client.post("/auth/signup", json=credentials)
    wrong = {"email": credentials["email"], "password": "wrongwrong"}

    for _ in range(settings.MAX_FAILED_LOGINS):
        assert client.post("/auth/token", json=wrong).status_code == 401

    r = client.post("/auth/token", json=wrong)
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) > 0

    # 잠금은 비밀번호가 맞아도 풀리지 않는다
    correct = {"email": credentials["email"], "password": credentials["password"]}
    assert client.post("/auth/token", json=correct).status_code == 429
