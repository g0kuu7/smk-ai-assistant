from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from backend.utils import normalize_text


LITHUANIAN_WEEKDAYS = {
    0: "pirmadienis",
    1: "antradienis",
    2: "trečiadienis",
    3: "ketvirtadienis",
    4: "penktadienis",
    5: "šeštadienis",
    6: "sekmadienis",
}

LITHUANIAN_MONTHS = {
    1: "sausio",
    2: "vasario",
    3: "kovo",
    4: "balandžio",
    5: "gegužės",
    6: "birželio",
    7: "rugsėjo",
    8: "rugpjūčio",
    9: "rugsėjo",
    10: "spalio",
    11: "lapkričio",
    12: "gruodžio",
}


def make_response(reply: str, links: list | None = None) -> dict:
    return {
        "reply": reply,
        "links": links or []
    }


def clean_message(user_message: str) -> str:
    message = normalize_text(user_message)

    for symbol in ["!", "?", ".", ",", ";", ":", "…", "-", "–", "_", "(", ")", "[", "]"]:
        message = message.replace(symbol, " ")

    return " ".join(message.split()).strip()


def get_current_datetime() -> datetime:
    try:
        return datetime.now(ZoneInfo("Europe/Vilnius"))
    except ZoneInfoNotFoundError:
        return datetime.now()


def recent_assistant_was_offering_help(history: list[dict] | None) -> bool:
    history = history or []

    recent_assistant_messages = [
        normalize_text(item.get("text", ""))
        for item in history[-5:]
        if item.get("role") == "assistant"
    ]

    combined = " ".join(recent_assistant_messages)

    help_phrases = [
        "kaip galiu jums padeti",
        "kuo galiu padeti",
        "gali paklausti",
        "galite klausti",
        "galiu padeti",
        "turi klausimu",
        "laukiu jusu klausimu",
        "parasykite savo klausima",
        "parasykite konkretu klausima",
        "apie studijas",
        "apie stojima",
        "apie studiju programas",
    ]

    return any(phrase in combined for phrase in help_phrases)


def try_handle_utility(user_message: str, history: list[dict] | None = None) -> dict | None:
    message = clean_message(user_message)

    greetings = {
        "labas",
        "sveiki",
        "sveikas",
        "sveika",
        "laba diena",
        "labukas",
        "hey",
        "hello",
        "hi",
    }

    if message in greetings:
        return make_response(
            "Sveiki! Kaip galiu Jums padėti? Galite klausti apie studijų programas, kainas, stojimą, kontaktus, Moodle, Classter ar kitą SMK informaciją."
        )

    # Tik realūs „turiu klausimų“ tipo sakiniai.
    # Svarbu: čia nebėra „turėčiau“, nes tada sakinys
    # „Kokius klausimus turėčiau užduoti sau...“ buvo klaidingai pagaunamas.
    if (
        any(word in message for word in ["turiu", "turio"])
        and any(word in message for word in ["klausim", "klausimeli", "klausimeliu"])
    ):
        return make_response(
            "Puiku — parašykite savo klausimą, ir pabandysiu atsakyti kuo aiškiau. Galite klausti apie studijų programas, kainas, stojimą, kontaktus arba studentų sistemas."
        )

    positive_followups = {
        "taip",
        "taip turiu",
        "turiu",
        "jo",
        "aha",
        "ok",
        "gerai",
        "zinoma",
        "noreciau",
    }

    if message in positive_followups and recent_assistant_was_offering_help(history):
        return make_response(
            "Puiku — parašykite konkretų klausimą, ir pabandysiu padėti kuo tiksliau."
        )

    negative_followups = {
        "ne",
        "neturiu",
        "ne dabar",
        "kol kas ne",
        "nereikia",
    }

    if message in negative_followups and recent_assistant_was_offering_help(history):
        return make_response(
            "Gerai. Jei vėliau prireiks informacijos apie SMK studijas, stojimą, kainas ar studentų sistemas, tiesiog parašykite."
        )

    if any(word in message for word in ["aciu", "dekui", "dekoju"]):
        return make_response(
            "Prašom! Jei turėsite daugiau klausimų apie SMK studijas, stojimą, kainas ar studentų sistemas, drąsiai klauskite."
        )

    if any(phrase in message for phrase in [
        "kaip sekasi",
        "kaip laikaisi",
        "kaip tau sekasi",
        "kaip tavo diena",
        "kaip jums diena",
        "kaip gyveni",
    ]):
        return make_response(
            "Ačiū, viskas gerai! Esu pasiruošęs padėti su klausimais apie SMK studijų programas, stojimą, kainas, kontaktus ar studentų sistemas."
        )

    if any(phrase in message for phrase in [
        "kas tu",
        "kas tu esi",
        "kuo tu gali padeti",
        "ka tu moki",
        "ka gali",
    ]):
        return make_response(
            "Esu SMK virtualus asistentas. Galiu padėti rasti informaciją apie studijų programas, kainas, stojimą, kontaktus, trumpąsias studijas, profesinį mokymą, Moodle, Classter ir kitus studentams aktualius dalykus."
        )

    if any(word in message for word in ["oras", "orai", "temperatura", "prognoze"]):
        return make_response(
            "Oro prognozės pateikti negaliu, nes esu skirtas SMK informacijai. Galiu padėti su studijų programomis, kainomis, stojimu, kontaktais, Moodle ar Classter."
        )

    if any(phrase in message for phrase in [
        "kokia diena siandien",
        "kokia siandien diena",
        "siandienos data",
        "kokia data siandien",
        "kelinta siandien",
        "kokia data",
    ]):
        try:
            now = get_current_datetime()
            weekday = LITHUANIAN_WEEKDAYS[now.weekday()]
            month = LITHUANIAN_MONTHS[now.month]

            return make_response(
                f"Šiandien yra {now.year} m. {month} {now.day} d., {weekday}."
            )
        except Exception:
            return make_response("Šiuo metu nepavyko nustatyti datos.")

    if any(phrase in message for phrase in [
        "kiek valandu",
        "kiek dabar valandu",
        "koks laikas",
        "kelinta valanda",
        "kelinta dabar",
    ]):
        try:
            now = get_current_datetime()
            return make_response(f"Dabar yra {now.strftime('%H:%M')} val.")
        except Exception:
            return make_response("Šiuo metu nepavyko nustatyti laiko.")

    return None