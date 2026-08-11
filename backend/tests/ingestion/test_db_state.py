"""적재 결과 확인"""

import pytest
from sqlalchemy import create_engine, text

from app.core.config import settings


@pytest.fixture(scope="module")
def conn():
    with create_engine(settings.DIRECT_URL).connect() as c:
        yield c


@pytest.mark.db
def test_counts_by_type(conn):
    counts = dict(conn.execute(text("select type, count(*) from contents group by type")).all())

    assert counts.get("MOVIE", 0) > 2900
    assert counts.get("BOOK", 0) > 900


@pytest.mark.db
def test_required_fields_filled(conn):
    empty = conn.execute(
        text("select count(*) from contents where title = '' or cardinality(genre) = 0")
    ).scalar()

    assert empty == 0
