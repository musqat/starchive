"""MovieLens 평점을 시드 유저로 적재

시드는 로그인할 수 없다 — 이메일이 예약 TLD(.invalid) 이고 비밀번호 해시가 아무도 모르는 값이다.
is_seed 필터를 빠뜨려도 인증이 뚫리지 않게 하려는 것.
"""

import secrets
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.security import hash_password
from app.domains.content.models import Content
from app.domains.user.models import ContentStatus, User, UserContent
from app.ingestion.db import Session
from app.ingestion.movielens import load_ratings

DATA_DIR = Path("data/ml-latest-small")
BATCH = 5000


def seed_email(movielens_user_id: str) -> str:
    return f"seed-{movielens_user_id}@movielens.invalid"


def main() -> None:
    with Session() as session:
        known_ids = set(session.scalars(select(Content.id)))
        print(f"수집된 콘텐츠 {len(known_ids):,}건")

        rows = list(load_ratings(DATA_DIR, known_ids))
        print(f"옮길 평점 {len(rows):,}건")

        # 1. 시드 유저 — 이미 있으면 건드리지 않는다
        movielens_ids = sorted({r.movielens_user_id for r in rows}, key=int)
        unusable = hash_password(secrets.token_urlsafe(32))
        session.execute(
            insert(User)
            .values(
                [
                    {
                        "email": seed_email(mid),
                        "password_hash": unusable,
                        "nickname": f"seed-{mid}",
                        "is_seed": True,
                    }
                    for mid in movielens_ids
                ]
            )
            .on_conflict_do_nothing(index_elements=["email"])
        )
        session.commit()

        user_id_by_movielens = {
            email.rsplit("@", 1)[0].removeprefix("seed-"): uid
            for uid, email in session.execute(
                select(User.id, User.email).where(User.is_seed.is_(True))
            )
        }
        print(f"시드 유저 {len(user_id_by_movielens):,}명")

        # 2. 평점 — 시드는 평점만 남긴다. 좋아요·추천·댓글이 없다
        records = [
            {
                "user_id": user_id_by_movielens[r.movielens_user_id],
                "content_id": r.content_id,
                "status": ContentStatus.DONE,
                "rating": r.rating,
            }
            for r in rows
        ]
        for start in range(0, len(records), BATCH):
            chunk = records[start : start + BATCH]
            session.execute(
                insert(UserContent)
                .values(chunk)
                .on_conflict_do_nothing(index_elements=["user_id", "content_id"])
            )
            session.commit()
            print(f"  {min(start + BATCH, len(records)):,} / {len(records):,}")


main()
