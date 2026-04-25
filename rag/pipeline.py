from backend.utils import normalize_text
from rag.retriever import Retriever
from rag.generator import GeminiGenerator
from rag.query_rewriter import rewrite_query


PROGRAMAVIMAS_IR_MULTIMEDIJA_URL = "https://smk.lt/studiju-programos/programavimo-studijos-ir-multimedija/"
STUDIJU_PROGRAMOS_URL = "https://smk.lt/studiju-programos/"
MOODLE_URL = "https://moodle.smk.lt/"
CLASSTER_URL = "https://studentams.smk.lt/"
STUDENTAMS_URL = "https://smk.lt/studentams/"
KONTAKTAI_URL = "https://smk.lt/kontaktai/"
PRIEMIMAS_URL = "https://smk.lt/stojimas/"


def query_is_too_vague_or_not_smk(query: str) -> bool:
    query_norm = normalize_text(query)

    command_like = any(
        query_norm.startswith(prefix)
        for prefix in ["python ", "pip ", "npm ", "node ", "git ", "flask "]
    )

    out_of_scope = any(word in query_norm for word in [
        "futbol",
        "rungtyn",
        "krepsin",
        "politika",
        "oras",
        "orai",
        "parasyk c++",
        "burbulin",
    ])

    return command_like or out_of_scope


def intent_bucket(query: str) -> str:
    q = normalize_text(query)

    if any(word in q for word in ["moodle", "classter", "tvarkarast", "uzduot", "pazym", "prisijung"]):
        return "student_systems"

    if any(word in q for word in ["kontakt", "adresas", "telefon", "el pastas", "vilni", "vilnu", "kaun", "klaiped"]):
        return "contacts"

    if any(word in q for word in ["stoj", "priem", "dokument", "registracij", "po 12"]):
        return "admission"

    if any(word in q for word in ["kaina", "kainuoja", "mokestis", "eur", "semestr", "metus"]):
        return "price"

    if any(word in q for word in ["programav", "multimed", "zaidim", "animacij", "it", "technolog", "programu", "studiju", "programa"]):
        return "programs"

    if any(word in q for word in ["trump", "kvalifikacij"]):
        return "short_cycle"

    return "general_smk"


def is_relevant_link(query: str, result) -> bool:
    query_norm = normalize_text(query)
    bucket = intent_bucket(query)
    category = normalize_text(str(result.metadata.get("category", "")))
    name = normalize_text(str(result.metadata.get("name", "")))
    text = normalize_text(result.text)
    url = normalize_text(str(result.metadata.get("url", "") or ""))

    if bucket == "student_systems":
        if "moodle" in query_norm:
            return "moodle" in name or "moodle" in text or "moodle" in url
        if "classter" in query_norm or "pazym" in query_norm or "tvarkarast" in query_norm:
            return "classter" in name or "studentams.smk.lt" in url or "classter" in text
        return category == "student_resource" and any(word in name + " " + text + " " + url for word in ["moodle", "classter", "studentams"])

    if bucket == "contacts":
        return category == "contact" or "kontakt" in url

    if bucket == "admission":
        return category in {"admission", "pdf", "faq"} or "stoj" in url or "priem" in url

    if bucket == "price":
        if "programav" in query_norm and "multimed" in query_norm:
            return "programavimas ir multimedija" in name or "programavimas ir multimedija" in text or category == "price"
        return category in {"price", "program"}

    if bucket == "programs":
        if "programav" in query_norm and "multimed" in query_norm:
            return "programavimas ir multimedija" in name or "programavimas ir multimedija" in text
        if "zaidim" in query_norm or "animacij" in query_norm:
            return "zaidimai" in name or "animacija" in name or "zaidimai" in text or "animacija" in text
        return category in {"program", "short_cycle", "professional_training", "faq"}

    if bucket == "short_cycle":
        return category in {"short_cycle", "faq", "admission"}

    return False


def prettify_label(result) -> str:
    category = result.metadata.get("category", "")
    name = result.metadata.get("name", "")
    url = str(result.metadata.get("url", "") or "")

    if "moodle" in url.lower() or "moodle" in str(name).lower():
        return "Moodle"

    if "studentams.smk.lt" in url.lower() or "classter" in str(name).lower():
        return "Classter"

    if category == "contact":
        return f"{name} kontaktai" if name else "Kontaktai"

    if category == "program":
        return f"Atidaryti programą: {name}" if name else "Atidaryti programą"

    if category == "price":
        return "Studijų programos"

    if category == "student_resource":
        return name or "Studentams"

    if category == "admission":
        return "Stojimas"

    if category == "short_cycle":
        return "Trumpųjų studijų informacija"

    if category == "professional_training":
        return "Profesinio mokymo informacija"

    if category == "pdf":
        return f"PDF: {name}" if name else "PDF dokumentas"

    return result.metadata.get("link_label") or "Atidaryti šaltinį"


def build_links(query: str, results: list) -> list[dict]:
    if query_is_too_vague_or_not_smk(query):
        return []

    query_norm = normalize_text(query)
    bucket = intent_bucket(query)
    links = []
    seen_urls = set()
    seen_labels = set()

    if "programav" in query_norm and "multimed" in query_norm:
        links.append({"label": "Programavimas ir multimedija", "url": PROGRAMAVIMAS_IR_MULTIMEDIJA_URL})
        seen_urls.add(PROGRAMAVIMAS_IR_MULTIMEDIJA_URL)
        seen_labels.add("Programavimas ir multimedija")

    if bucket == "student_systems":
        if "moodle" in query_norm:
            links.append({"label": "Moodle", "url": MOODLE_URL})
            seen_urls.add(MOODLE_URL)
            seen_labels.add("Moodle")
        if "classter" in query_norm or "tvarkarast" in query_norm or "pazym" in query_norm:
            links.append({"label": "Classter", "url": CLASSTER_URL})
            seen_urls.add(CLASSTER_URL)
            seen_labels.add("Classter")
        if not links:
            links.extend([
                {"label": "Classter", "url": CLASSTER_URL},
                {"label": "Moodle", "url": MOODLE_URL},
                {"label": "Studentams", "url": STUDENTAMS_URL},
            ])
            seen_urls.update([CLASSTER_URL, MOODLE_URL, STUDENTAMS_URL])
            seen_labels.update(["Classter", "Moodle", "Studentams"])

    if bucket == "contacts" and not links:
        links.append({"label": "Kontaktai", "url": KONTAKTAI_URL})
        seen_urls.add(KONTAKTAI_URL)
        seen_labels.add("Kontaktai")

    if bucket == "admission" and not links:
        links.append({"label": "Stojimas", "url": PRIEMIMAS_URL})
        seen_urls.add(PRIEMIMAS_URL)
        seen_labels.add("Stojimas")

    for result in results:
        if not is_relevant_link(query, result):
            continue

        url = str(result.metadata.get("url", "") or "").strip()
        if not url or url in seen_urls:
            continue

        label = prettify_label(result)
        if label in seen_labels:
            continue

        seen_urls.add(url)
        seen_labels.add(label)
        links.append({"label": label, "url": url})

        if len(links) >= 3:
            break

    if not links and bucket in {"programs", "price", "short_cycle"}:
        links.append({"label": "Visos studijų programos", "url": STUDIJU_PROGRAMOS_URL})

    return links[:3]


def clean_reply(text: str) -> str:
    text = text.strip()

    if text.startswith("Klausimas:") and "Atsakymas:" in text:
        text = text.split("Atsakymas:", 1)[1].strip()

    replacements = [
        "Pagal pateiktą informaciją, ",
        "Pagal pateiktą informaciją ",
        "Turimoje informacijoje, ",
        "Turimoje informacijoje ",
        "Remiantis pateikta informacija, ",
        "Remiantis pateikta informacija ",
    ]

    for item in replacements:
        text = text.replace(item, "")

    bad_link_phrases = [
        "Deja, tiesioginio programos aprašymo nuorodos neturiu.",
        "Deja, tiesioginės programos aprašymo nuorodos neturiu.",
        "Tiesioginės nuorodos neturiu.",
    ]

    for phrase in bad_link_phrases:
        text = text.replace(phrase, "Programos nuorodą pateikiu žemiau.")

    return text.strip()


def answer_with_rag(user_message: str, history: list[dict] | None = None) -> dict | None:
    history = history or []

    if query_is_too_vague_or_not_smk(user_message):
        return None

    search_query = rewrite_query(user_message, history)

    retriever = Retriever()
    results = retriever.retrieve(search_query, top_k=6)

    if not results:
        return None

    best_score = results[0].score

    # Griežtesnis slenkstis, kad RAG neatsakinėtų nesusijusiomis temomis.
    if best_score > 0.68:
        return None

    context_chunks = [result.text for result in results[:4]]
    links = build_links(user_message, results)

    generator = GeminiGenerator()

    try:
        reply = generator.generate(user_message, context_chunks, history)
    except Exception as error:
        print("[GENERATOR ERROR]", repr(error))
        return None

    reply = clean_reply(reply)

    if not reply or reply.lower() == "neradau tikslios informacijos.":
        return None

    return {
        "reply": reply,
        "links": links
    }