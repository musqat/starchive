import csv
from collections import Counter
from pathlib import Path


def load_target_tmdb_ids(data_dir: Path, limit: int = 3000) -> list[int]:
    """평점 수 상위 limit 개 영화의 tmdbId 목록"""
    with (data_dir / "ratings.csv").open(encoding="utf-8") as f:
        counts = Counter(row["movieId"] for row in csv.DictReader(f))
    top = counts.most_common(limit)  # [("356", 329), ("318", 317), ...]
    with (data_dir / "links.csv").open(encoding="utf-8") as f:
        links = {row["movieId"]: row["tmdbId"] for row in csv.DictReader(f) if row["tmdbId"]}
    return [int(links[mid]) for mid, _ in top if mid in links]
