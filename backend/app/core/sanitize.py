"""사용자가 넣는 공개 텍스트에서 HTML 태그를 걷어낸다

메모·닉네임은 공개 메모 응답으로 다른 사용자에게 나간다. 지금 React 가 렌더에서
이스케이프하지만, 모바일·서드파티 클라이언트가 붙거나 dangerouslySetInnerHTML 을
쓰면 저장형 XSS 가 된다. 저장 전에 한 겹 더 막는다
"""

import re

# HTML 태그는 `<` 다음에 알파벳이나 `/` 가 온다. `a < b`, `3<5` 는 안 건드린다
_TAG = re.compile(r"</?[a-zA-Z][^>]*>")


def strip_tags(text: str) -> str:
    return _TAG.sub("", text)
