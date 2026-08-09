import pytest


@pytest.mark.db
def test_list(client):
    r = client.get("/contents?size=5")

    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 5
    assert body["total"] > len(body["items"])  # 전체는 페이지보다 많다
    assert body["page"] == 1
    assert body["size"] == 5


@pytest.mark.db
def test_search(client):
    r = client.get("/contents", params={"q": "반지의", "size": 5})

    assert r.status_code == 200
    body = r.json()
    assert body["items"], "검색 결과가 비었다"
    assert all("반지의" in row["title"] for row in body["items"])
    assert body["total"] == len(body["items"])  # 5개 이하라 한 페이지에 다 들어온다


@pytest.mark.db
def test_filter_by_type(client):
    movies = client.get("/contents", params={"type": "MOVIE", "size": 1}).json()
    books = client.get("/contents", params={"type": "BOOK", "size": 1}).json()

    assert movies["total"] > 0
    assert books["total"] == 0  # 아직 책은 수집 전
    assert all(row["type"] == "MOVIE" for row in movies["items"])


@pytest.mark.db
def test_detail(client):
    r = client.get("/contents/tmdb_278")

    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "tmdb_278"
    assert body["title"]
    assert "description" in body  # Summary 가 아니라 Detail 스키마인지


@pytest.mark.db
def test_detail_404(client):
    r = client.get("/contents/nope")

    assert r.status_code == 404
    assert r.json() == {"detail": "content not found"}


@pytest.mark.parametrize("params", [{"page": 0}, {"size": 0}, {"size": 101}])
def test_query_validation(client, params):
    assert client.get("/contents", params=params).status_code == 422


@pytest.mark.db
def test_search_empty(client):
    r = client.get("/contents", params={"q": "존재하지않는영화제목"})

    assert r.status_code == 200
    body = r.json()
    assert body["items"] == []
    assert body["total"] == 0