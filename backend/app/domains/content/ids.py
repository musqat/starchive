def make_content_id(source: str, external_id: str | int) -> str:
    return f"{source.lower()}_{external_id}"
