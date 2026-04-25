from backend.utils import normalize_text


BLOCKED_PATTERNS = [
    "nulauz",
    "hack",
    "apeik sistema",
    "sukciau",
    "apgauti",
    "vogti",
    "kenkejisk",
]


def try_handle_unsafe(user_message: str) -> dict | None:
    message = normalize_text(user_message)

    if any(pattern in message for pattern in BLOCKED_PATTERNS):
        return {
            "reply": "Negaliu padėti su pavojingais, neteisėtais ar kenkėjiškais veiksmais.",
            "links": []
        }

    return None