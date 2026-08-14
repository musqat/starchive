import pytest

MOVIE = "tmdb_157336"  # 인터스텔라
BOOK = "aladin_9788937460586"  # 싯다르타


@pytest.mark.db  # 기록 생성 → 200
def test_upsert_creates(auth_client):
    r = auth_client.put(f"/me/records/{MOVIE}", json={"status": "WISH"})

    assert r.status_code == 200
    body = r.json()
    assert body["content_id"] == MOVIE
    assert body["status"] == "WISH"
    assert body["recommended"] is False

@pytest.mark.db  # recommended=true → status 도 DONE
def test_recommend_forces_done(auth_client):
    auth_client.put(f"/me/records/{MOVIE}", json={"status": "WISH"})
    r = auth_client.put(f"/me/records/{MOVIE}", json={"recommended": True})

    assert r.json()["recommended"] is True
    assert r.json()["status"] == "DONE"

@pytest.mark.db  # 보내지 않은 필드는 유지
def test_partial_update(auth_client):
    auth_client.put(f"/me/records/{MOVIE}", json={"status": "WISH"})
    r = auth_client.put(f"/me/records/{MOVIE}", json={"recommended": False})

    assert r.json()["status"] == "WISH"
    assert r.json()["recommended"] is False


@pytest.mark.db  # 추천이 켜져 있으면 status 를 WISH 로 되돌릴 수 없음
def test_status_locked_while_recommended(auth_client):
    auth_client.put(f"/me/records/{MOVIE}", json={"recommended": True})
    r = auth_client.put(f"/me/records/{MOVIE}", json={"status": "WISH"})

    assert r.json()["status"] == "DONE"

    # 추천을 끄면 바꿀 수 있다
    auth_client.put(f"/me/records/{MOVIE}", json={"recommended": False})
    r = auth_client.put(f"/me/records/{MOVIE}", json={"status": "WISH"})
    assert r.json()["status"] == "WISH"


@pytest.mark.db  # 없는 콘텐츠 → 404
def test_unknown_content(auth_client):
    r = auth_client.put("/me/records/tmdb_123456780", json={"status": "WISH"})
    assert r.status_code == 404

@pytest.mark.db  # status·type 으로 걸러짐
def test_library_filters(auth_client):
    auth_client.put(f"/me/records/{MOVIE}", json={"status": "WISH"})
    auth_client.put(f"/me/records/{BOOK}", json={"status": "DONE"})

    lib = auth_client.get("/me/library", params={"type": "MOVIE"}).json()
    assert [x["content_id"] for x in lib] == [MOVIE]


@pytest.mark.db  # 삭제 → 204, 서재에서 사라짐
def test_delete(auth_client):
    auth_client.put(f"/me/records/{MOVIE}", json={"status": "WISH"})
    assert auth_client.delete(f"/me/records/{MOVIE}").status_code == 204
    assert auth_client.get("/me/library").json() == []

@pytest.mark.db  # 비로그인 → 401
def test_requires_login(client):
    assert client.get("/me/library").status_code == 401

@pytest.mark.db  # 평점을 매기면 status 도 DONE
def test_rating_forces_done(auth_client):
    r = auth_client.put(f"/me/records/{MOVIE}", json={"rating": 4})

    assert r.json()["status"] == "DONE"
    assert r.json()["rating"] == 4


@pytest.mark.db  # rating 과 recommended 는 독립
def test_rating_and_recommended_independent(auth_client):
    auth_client.put(f"/me/records/{MOVIE}", json={"rating": 5, "recommended": True})
    r = auth_client.put(f"/me/records/{MOVIE}", json={"rating": 2})

    assert r.json()["rating"] == 2
    assert r.json()["recommended"] is True


@pytest.mark.db  # null 을 보내면 평점이 지워짐
def test_rating_cleared_by_null(auth_client):
    auth_client.put(f"/me/records/{MOVIE}", json={"rating": 3})
    r = auth_client.put(f"/me/records/{MOVIE}", json={"rating": None})

    assert r.json()["rating"] is None
    assert r.json()["status"] == "DONE"  # 봤다는 사실은 남는다


@pytest.mark.db  # 1~5 밖 → 422
@pytest.mark.parametrize("value", [0, 6])
def test_rating_out_of_range(auth_client, value):
    assert auth_client.put(f"/me/records/{MOVIE}", json={"rating": value}).status_code == 422


@pytest.mark.db  # 상세에 my_rating 이 붙음
def test_my_rating_attached(auth_client):
    auth_client.put(f"/me/records/{MOVIE}", json={"rating": 4})

    assert auth_client.get(f"/contents/{MOVIE}").json()["my_rating"] == 4

@pytest.mark.db  # 좋아요를 켜면 status 도 DONE
def test_liked_forces_done(auth_client):
    r = auth_client.put(f"/me/records/{MOVIE}", json={"liked": True})

    assert r.json()["liked"] is True
    assert r.json()["status"] == "DONE"


@pytest.mark.db  # 좋아요·평점·추천은 서로 독립
def test_liked_independent(auth_client):
    auth_client.put(f"/me/records/{MOVIE}", json={"liked": True, "recommended": True, "rating": 5})
    r = auth_client.put(f"/me/records/{MOVIE}", json={"liked": False})

    body = r.json()
    assert body["liked"] is False
    assert body["recommended"] is True
    assert body["rating"] == 5


@pytest.mark.db  # 상세에 my_liked 가 붙음
def test_my_liked_attached(auth_client):
    auth_client.put(f"/me/records/{MOVIE}", json={"liked": True})

    assert auth_client.get(f"/contents/{MOVIE}").json()["my_liked"] is True


@pytest.mark.db  # 보관함을 liked·recommended 로 거름
def test_library_filters_by_signal(auth_client):
    auth_client.put(f"/me/records/{MOVIE}", json={"liked": True})
    auth_client.put(f"/me/records/{BOOK}", json={"recommended": True})

    liked = auth_client.get("/me/library", params={"liked": True}).json()
    recommended = auth_client.get("/me/library", params={"recommended": True}).json()

    assert [x["content_id"] for x in liked] == [MOVIE]
    assert [x["content_id"] for x in recommended] == [BOOK]
