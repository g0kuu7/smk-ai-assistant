import re
from backend.utils import normalize_text


def slugify(text: str) -> str:
    text = normalize_text(text)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")