"""공개 텍스트 태그 제거 — 저장형 XSS 방어"""

import pytest
from pydantic import ValidationError

from app.core.sanitize import strip_tags
from app.domains.user.schemas import RecordIn, SignUpIn


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("<script>alert(document.cookie)</script>", "alert(document.cookie)"),
        ("<b>굵게</b>", "굵게"),
        ("<img src=x onerror=alert(1)>야옹", "야옹"),
        # 태그가 아닌 꺾쇠는 남긴다
        ("a < b 이고 c > d", "a < b 이고 c > d"),
        ("3<5 는 참", "3<5 는 참"),
        ("평범한 메모", "평범한 메모"),
    ],
)
def test_strip_tags(raw, expected):
    assert strip_tags(raw) == expected


def test_memo_tag_removed():
    record = RecordIn(memo="<script>alert(1)</script>좋았다")
    assert record.memo == "alert(1)좋았다"
    assert "<script>" not in record.memo


def test_nickname_tag_removed():
    user = SignUpIn(email="a@b.com", password="secret1234", nickname="<b>홍길동</b>")
    assert user.nickname == "홍길동"


def test_nickname_only_tags_rejected():
    with pytest.raises(ValidationError):
        SignUpIn(email="a@b.com", password="secret1234", nickname="<b></b>")
