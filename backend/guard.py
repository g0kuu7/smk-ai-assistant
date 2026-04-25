import re
from collections import Counter

from backend.utils import normalize_text


def make_response(reply: str) -> dict:
    return {
        "reply": reply,
        "links": []
    }


def is_mostly_symbols(text: str) -> bool:
    if not text:
        return False

    symbol_count = sum(1 for ch in text if not ch.isalnum() and not ch.isspace())
    return symbol_count > len(text) * 0.45


def has_too_many_repeated_chars(text: str) -> bool:
    return bool(re.search(r"(.)\1{7,}", text))


def looks_like_gibberish(text: str) -> bool:
    words = text.split()
    if not words:
        return False

    # labai daug trumpų keistų žodžių
    weird_words = 0
    for word in words:
        cleaned = re.sub(r"[^a-zA-ZąčęėįšųūžĄČĘĖĮŠŲŪŽ0-9]", "", word)
        if cleaned and len(cleaned) >= 6:
            vowels = sum(1 for ch in cleaned.lower() if ch in "aeiouyąčęėįšųūž")
            if vowels <= 1:
                weird_words += 1

    return weird_words >= max(2, len(words) // 2)


def too_many_unique_repeats(text: str) -> bool:
    words = [w for w in normalize_text(text).split() if w]
    if len(words) < 6:
        return False

    counts = Counter(words)
    most_common_count = counts.most_common(1)[0][1]
    return most_common_count >= len(words) * 0.6


def try_block_low_value_message(user_message: str) -> dict | None:
    raw = user_message.strip()
    message = normalize_text(user_message)

    if not raw:
        return make_response("Įrašyk klausimą, ir pabandysiu padėti.")

    if len(raw) > 1200:
        return make_response(
            "Klausimas per ilgas. Pabandyk parašyti trumpiau arba padalinti į kelias dalis."
        )

    if len(message) <= 1:
        return make_response(
            "Nesu tikras, ko klausi. Pabandyk parašyti aiškesnį klausimą."
        )

    if len(message.split()) == 1 and len(message) <= 2:
        return make_response(
            "Pabandyk suformuluoti aiškesnį klausimą."
        )

    if is_mostly_symbols(raw):
        return make_response(
            "Pabandyk parašyti klausimą žodžiais."
        )

    if has_too_many_repeated_chars(raw):
        return make_response(
            "Pabandyk parašyti klausimą be pasikartojančių simbolių."
        )

    if looks_like_gibberish(message):
        return make_response(
            "Nesu tikras, ką turi omenyje. Pabandyk suformuluoti klausimą aiškiau."
        )

    if too_many_unique_repeats(message):
        return make_response(
            "Atrodo, kad klausime daug pasikartojimų. Pabandyk parašyti trumpiau ir aiškiau."
        )

    return None