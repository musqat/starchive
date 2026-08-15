import csv
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

from app.domains.content.ids import make_content_id


def _links(data_dir: Path) -> dict[str, str]:
    """movieId → tmdbId"""
    with (data_dir / "links.csv").open(encoding="utf-8") as f:
        return {row["movieId"]: row["tmdbId"] for row in csv.DictReader(f) if row["tmdbId"]}


def load_target_tmdb_ids(data_dir: Path, limit: int = 3000) -> list[int]:
    """평점 수 상위 limit 개 영화의 tmdbId 목록"""
    with (data_dir / "ratings.csv").open(encoding="utf-8") as f:
        counts = Counter(row["movieId"] for row in csv.DictReader(f))
    top = counts.most_common(limit)  # [("356", 329), ("318", 317), ...]
    links = _links(data_dir)
    return [int(links[mid]) for mid, _ in top if mid in links]


class SeedRating(NamedTuple):
    movielens_user_id: str
    content_id: str  # tmdb_157336
    rating: float  # 0.5 ~ 5.0


def load_ratings(data_dir: Path, known_ids: set[str]) -> Iterator[SeedRating]:
    """ratings.csv를 content_id 로 옮긴다
    수집하지 않은 영화의 평점은 건너뛴다.
    상위 3,000편 기준으로 약 86%정도 수집
    """
    links = _links(data_dir)
    with (data_dir / "ratings.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tmdb_id = links.get(row["movieId"])
            if not tmdb_id:
                continue
            content_id = make_content_id("TMDB", tmdb_id)
            if content_id not in known_ids:
                continue
            yield SeedRating(row["userId"], content_id, float(row["rating"]))
