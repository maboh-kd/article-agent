import re

def summarize(text: str, max_chars: int = 140) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]
