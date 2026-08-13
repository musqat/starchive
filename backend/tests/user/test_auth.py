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
    assert auth_client.get("/auth/me").status_code == 200    # 로그인 상태 확인
    assert auth_client.post("/auth/logout").status_code == 204
    assert auth_client.get("/auth/me").status_code == 401     # 쿠키 사라짐