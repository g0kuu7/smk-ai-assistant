from backend.utils import normalize_text


FOLLOW_UP_MARKERS = [
    "o ",
    "o?",
    "o tai",
    "o ka",
    "o ką",
    "ten",
    "tas",
    "ta",
    "jie",
    "ji",
    "jis",
    "kiek",
    "kaina",
    "kainuoja",
    "kur",
    "kada",
    "kaip",
]


def rewrite_query(user_message: str, history: list[dict] | None = None) -> str:
    history = history or []
    current = normalize_text(user_message)

    if not current:
        return user_message

    previous_user_messages = [
        item.get("text", "").strip()
        for item in history
        if item.get("role") == "user" and item.get("text", "").strip()
    ]

    # jei history gale jau yra tas pats current klausimas, išimam
    if previous_user_messages and normalize_text(previous_user_messages[-1]) == current:
        previous_user_messages = previous_user_messages[:-1]

    previous_user = previous_user_messages[-1] if previous_user_messages else ""

    short_follow_up = len(current.split()) <= 5
    has_followup_marker = any(current.startswith(marker) or marker in current for marker in FOLLOW_UP_MARKERS)

    if previous_user and (short_follow_up or has_followup_marker):
        return f"{previous_user}. {user_message}"

    return user_message