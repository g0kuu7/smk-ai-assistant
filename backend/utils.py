import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Paverčia tekstą į mažąsias raides, pašalina perteklinius tarpus
    ir lietuviškus diakritinius ženklus, kad paieška būtų lankstesnė.
    """
    if not text:
        return ""

    text = text.lower().strip()
    text = remove_lithuanian_diacritics(text)
    text = re.sub(r"\s+", " ", text)
    return text


def remove_lithuanian_diacritics(text: str) -> str:
    if not text:
        return ""

    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))