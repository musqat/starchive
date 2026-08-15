"""테스트가 남긴 계정 정리

E2E는 실행마다 계정을 새로 만들고 삭제를 안함 -> 쌓이면 통계 오염
Playwright globalTeardown으로 이 스크립트를 호출

수동 실행:
    uv run python -m scripts.cleanup_test_users          # 세기만
    uv run python -m scripts.cleanup_test_users --apply  # 삭제
"""

import sys

from sqlalchemy import func, or_, select

from app.domains.user.models import User
from app.ingestion.db import Session

# 테스트가 만드는 이메일 형태 (실계정과 안겹침)
PATTERNS = ("e2e-%@example.com", "test-%@example.com")


def condition():
    """시드는 절대 건드리지 않는다"""
    return (User.is_seed.is_(False)) & or_(*(User.email.like(p) for p in PATTERNS))


def main() -> None:
    with Session() as session:
        n = session.scalar(select(func.count()).where(condition()))
        if not n:
            print("정리할 계정 없음")
            return

        if "--apply" not in sys.argv:
            print(f"삭제 대상 {n:,}개 (--apply 를 붙이면 지운다)")
            return

        deleted = session.execute(User.__table__.delete().where(condition())).rowcount
        session.commit()
        print(f"삭제 {deleted:,}개")


main()
