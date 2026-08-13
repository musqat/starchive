import pytest


@pytest.mark.db
def test_list(client):
    r = client.get("/contents?size=5")

    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 5
    assert body["total"] > len(body["items"])  # 전체는 페이지보다 많음
    assert body["page"] == 1
    assert body["size"] == 5


@pytest.mark.db
def test_search(client):
    r = client.get("/contents", params={"q": "반지의", "size": 5})

    assert r.status_code == 200
    body = r.json()
    assert body["items"], "검색 결과가 비었음"
    assert all("반지의" in row["title"] for row in body["items"])
    assert body["total"] == len(body["items"])


@pytest.mark.db
def test_filter_by_type(client):
    movies = client.get("/contents", params={"type": "MOVIE", "size": 3}).json()
    books = client.get("/contents", params={"type": "BOOK", "size": 3}).json()
    both = client.get("/contents", params={"size": 3}).json()

    assert movies["total"] > 0
    assert books["total"] > 0
    assert all(row["type"] == "MOVIE" for row in movies["items"])
    assert all(row["type"] == "BOOK" for row in books["items"])
    assert both["total"] == movies["total"] + books["total"]


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


@pytest.mark.parametrize(
    "params",
    [{"page": 0}, {"size": 0}, {"size": 101}, {"sort": "cheapest"}, {"order": "sideways"}],
)
def test_query_validation(client, params):
    assert client.get("/contents", params=params).status_code == 422


@pytest.mark.db
def test_genres(client):
    movie = client.get("/contents/genres", params={"type": "MOVIE"}).json()
    book = client.get("/contents/genres", params={"type": "BOOK"}).json()

    assert "드라마" in movie
    assert "인문학" in book
    assert movie[0] == "드라마", "빈도 내림차순이 아님"
    # 액션·판타지 등 일부 이름은 두 타입에 다 있음. type 없이 genre 만 걸면 섞임
    assert set(movie) & set(book)


@pytest.mark.db
def test_genre_filter(client):
    r = client.get("/contents", params={"type": "MOVIE", "genre": "SF", "size": 5})

    body = r.json()
    assert body["total"] > 0
    assert all("SF" in row["genre"] for row in body["items"])


@pytest.mark.db
def test_sort_rating_excludes_low_vote_count(client):
    rated = client.get("/contents", params={"type": "MOVIE", "sort": "rating"}).json()
    everything = client.get("/contents", params={"type": "MOVIE"}).json()

    # 평가 수가 적은 항목은 평점순에서 제외
    assert rated["total"] < everything["total"]


@pytest.mark.db
def test_sort_rating_order(client):
    """external_rating 은 응답에 있어 순서를 직접 확인 가능"""

    def ratings(order: str):
        params = {"type": "MOVIE", "sort": "rating", "order": order, "size": 10}
        body = client.get("/contents", params=params).json()
        return [row["external_rating"] for row in body["items"]]

    desc = ratings("desc")
    asc = ratings("asc")

    assert desc == sorted(desc, reverse=True)
    assert asc == sorted(asc)
    assert desc[0] > asc[0]


@pytest.mark.db
@pytest.mark.parametrize("sort", ["popular", "recent"])
def test_sort_order_flips(client, sort):
    """정렬 기준값이 응답에 없어서 첫 항목이 바뀌는지만 확인"""

    def first_id(order: str):
        params = {"type": "MOVIE", "sort": sort, "order": order, "size": 1}
        return client.get("/contents", params=params).json()["items"][0]["id"]

    assert first_id("desc") != first_id("asc")


@pytest.mark.db
def test_search_empty(client):
    r = client.get("/contents", params={"q": "존재하지않는영화제목"})

    assert r.status_code == 200
    body = r.json()
    assert body["items"] == []
    assert body["total"] == 0
