from backend.utils import normalize_text


SMK_KEYWORDS = [
    "smk",
    "studij",
    "program",
    "kaina",
    "kainuoja",
    "mokestis",
    "stoj",
    "priem",
    "priemim",
    "kontakt",
    "adresas",
    "telefon",
    "moodle",
    "classter",
    "student",
    "vilnius",
    "kaunas",
    "klaipeda",
    "trump",
    "profesin",
    "kurs",
    "erasmus",
    "stipend",
    "motyv",
    "vertin",
    "dokument",
    "taisyk",
    "registracij",
    "atestat",
    "egzamin",
    "aukstesn",
    "priemimo",
]

GENERAL_EXPLANATION_PATTERNS = [
    "kas yra",
    "paaiskink",
    "paaiškink",
    "kaip veikia",
]

SMK_STRONG_SIGNALS = [
    "smk",
    "studij",
    "program",
    "kaina",
    "kainuoja",
    "stoj",
    "priem",
    "kontakt",
    "moodle",
    "classter",
    "vilnius",
    "kaunas",
    "klaipeda",
]


def _history_is_smk_related(history: list[dict] | None) -> bool:
    history = history or []
    recent_messages = history[-4:]

    combined = " ".join(
        normalize_text(item.get("text", ""))
        for item in recent_messages
    )

    return any(keyword in combined for keyword in SMK_KEYWORDS)


def classify_message(user_message: str, history: list[dict] | None = None) -> str:
    message = normalize_text(user_message)

    if not message:
        return "general"

    if any(pattern in message for pattern in GENERAL_EXPLANATION_PATTERNS):
        if not any(signal in message for signal in SMK_STRONG_SIGNALS):
            return "general"

    if any(keyword in message for keyword in SMK_KEYWORDS):
        return "smk"

    if len(message.split()) <= 5 and _history_is_smk_related(history):
        return "smk"

    return "general"