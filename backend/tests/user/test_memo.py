import pytest

MOVIE = "tmdb_157336"  # 인터스텔라

PASSWORD = "secret1234"


@pytest.mark.db  # 메모를 남기면 status 도 DONE
def test_memo_forces_done(auth_client):
    r = auth_client.put(f"/me/records/{MOVIE}", json={"memo": "좋았다"})

    assert r.json()["memo"] == "좋았다"
    assert r.json()["memo_public"] is False  # 기본은 비공개
    assert r.json()["status"] == "DONE"


@pytest.mark.db  # 빈 문자열을 보내면 지워짐
def test_memo_cleared(auth_client):
    auth_client.put(f"/me/records/{MOVIE}", json={"memo": "좋았다"})
    r = auth_client.put(f"/me/records/{MOVIE}", json={"memo": ""})

    assert r.json()["memo"] is None


@pytest.mark.db  # 500자 초과 → 422
def test_memo_too_long(auth_client):
    r = auth_client.put(f"/me/records/{MOVIE}", json={"memo": "가" * 501})
    assert r.status_code == 422


@pytest.mark.db  # 상세에 my_memo 가 붙음
def test_my_memo_attached(auth_client):
    auth_client.put(f"/me/records/{MOVIE}", json={"memo": "내 메모", "memo_public": True})

    detail = auth_client.get(f"/contents/{MOVIE}").json()
    assert detail["my_memo"] == "내 메모"
    assert detail["my_memo_public"] is True


@pytest.mark.db  # 비공개 메모는 목록에 안 나옴
def test_private_memo_hidden(auth_client, client):
    auth_client.put(f"/me/records/{MOVIE}", json={"memo": "비밀"})

    memos = client.get(f"/contents/{MOVIE}/memos").json()
    assert "비밀" not in [m["memo"] for m in memos]


@pytest.mark.db  # 공개 메모는 닉네임과 함께 나오고, 내 것은 빠진다
def test_public_memo_visible_to_others(auth_client, credentials):
    auth_client.put(f"/me/records/{MOVIE}", json={"memo": "공개함", "memo_public": True, "rating": 4})

    mine = auth_client.get(f"/contents/{MOVIE}/memos").json()
    assert "공개함" not in [m["memo"] for m in mine]  # 내 메모는 상세 응답에 있다

    auth_client.post("/auth/logout")
    others = auth_client.get(f"/contents/{MOVIE}/memos").json()
    row = next(m for m in others if m["memo"] == "공개함")
    assert row["nickname"] == credentials["nickname"]
    assert row["rating"] == 4


@pytest.mark.db  # has_memo 로 메모 남긴 것만 거름
def test_library_filters_by_memo(auth_client):
    BOOK = "aladin_9788937460586"
    auth_client.put(f"/me/records/{MOVIE}", json={"memo": "남김"})
    auth_client.put(f"/me/records/{BOOK}", json={"liked": True})

    with_memo = auth_client.get("/me/library", params={"has_memo": True}).json()

    assert [x["content_id"] for x in with_memo] == [MOVIE]
