from app.ingestion.normalizer import build_embedding_text


def test_모든_필드가_있으면_줄바꿈으로_묶는다():
    text = build_embedding_text(
        "싯다르타", ["소설/시/희곡", "독일소설"], "헤르만 헤세", "구도의 여정을 그린 소설"
    )

    assert text == "싯다르타\n소설/시/희곡, 독일소설\n헤르만 헤세\n구도의 여정을 그린 소설"


def test_줄거리가_없으면_만들지_않는다():
    """제목만으로 만든 벡터는 유사도가 이상하게 잡힘. 후보에서 제거"""
    assert build_embedding_text("어떤 만화", ["만화/라이트노벨"], "작가", None) is None
    assert build_embedding_text("어떤 만화", ["만화/라이트노벨"], "작가", "") is None


def test_빈_필드는_줄을_비우지_않는다():
    text = build_embedding_text("제목만 있는 것", None, None, "줄거리")

    assert text == "제목만 있는 것\n줄거리"
