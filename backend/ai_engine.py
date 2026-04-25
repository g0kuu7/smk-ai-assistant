import re
from typing import Any

from backend.data_loader import load_smk_data
from backend.guard import try_block_low_value_message
from backend.legacy_rule_engine import generate_answer as legacy_generate_answer
from backend.router import classify_message
from backend.safety import try_handle_unsafe
from backend.utility_engine import try_handle_utility
from backend.utils import normalize_text
from rag.consultant_generator import ConsultantGenerator


PROGRAMAVIMAS_IR_MULTIMEDIJA_URL = "https://smk.lt/studiju-programos/programavimo-studijos-ir-multimedija/"
KOMPIUTERINIAI_ZAIDIMAI_URL = "https://smk.lt/studiju-programos/kompiuteriniai-zaidimai-ir-animacija/"
STUDIJU_PROGRAMOS_URL = "https://smk.lt/studiju-programos/"
STUDENTAMS_URL = "https://smk.lt/studentams/"
MOODLE_URL = "https://moodle.smk.lt/"
CLASSTER_URL = "https://studentams.smk.lt/"
KONTAKTAI_URL = "https://smk.lt/kontaktai/"
PRIEMIMAS_URL = "https://smk.lt/stojimas/"


def make_response(reply: str, links: list | None = None) -> dict[str, Any]:
    return {
        "reply": reply,
        "links": links or []
    }


def has_any(text: str, patterns: list[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def get_recent_context(history: list[dict] | None) -> str:
    history = history or []

    return " ".join(
        normalize_text(item.get("text", ""))
        for item in history[-8:]
    )


def get_recent_user_context(history: list[dict] | None) -> str:
    history = history or []

    return " ".join(
        normalize_text(item.get("text", ""))
        for item in history[-6:]
        if item.get("role") == "user"
    )


def asks_for_confidential_file(user_message: str) -> bool:
    message = normalize_text(user_message)

    patterns = [
        ".env",
        "env fail",
        "api key",
        "api rakta",
        "api raktą",
        "gemini api",
        "slaptazodi",
        "slaptažodį",
        "token",
        "access token",
        "private key",
        "system prompt",
        "sistemos prompt",
        "sistemos prompta",
        "sistemos promta",
        "vidines instrukcijos",
        "vidinės instrukcijos",
        "parodyk instrukcijas",
        "parodyk savo instrukcijas",
        "atskleisk instrukcijas",
        "nekreipk demesi i taisykles",
        "nekreipk dėmesio į taisykles",
        "ignoruok taisykles",
        "ignore rules",
    ]

    return has_any(message, patterns)


def handle_confidential_request() -> dict[str, Any]:
    return make_response(
        "Negaliu dalintis konfidencialiais failais, API raktais ar vidinėmis sistemos instrukcijomis. Galiu padėti su SMK informacija: studijų programomis, kainomis, stojimu, kontaktais, Moodle ar Classter."
    )


def asks_out_of_scope_question(user_message: str) -> bool:
    message = normalize_text(user_message)

    command_like = bool(
        re.search(r"(^|\s)(python|pip|npm|node|flask|uvicorn|git)\s+[-\w]", message)
    )

    out_of_scope_patterns = [
        "futbol",
        "rungtyn",
        "kas laimejo",
        "kas laimėjo",
        "krepsin",
        "krepšin",
        "naujienos",
        "politika",
        "parasyk c++",
        "parašyk c++",
        "parasyk koda",
        "parašyk kodą",
        "burbulin",
        "surikiavim",
    ]

    math_like = bool(re.search(r"\d+\s*[\+\-\*\/]\s*\d+", message))

    return (
        command_like
        or has_any(message, out_of_scope_patterns)
        or ("kiek yra" in message and math_like)
    )


def handle_out_of_scope_question() -> dict[str, Any]:
    return make_response(
        "Šis asistentas skirtas SMK informacijai, todėl galiu padėti su studijų programomis, kainomis, stojimu, kontaktais, Moodle, Classter ar kitais su SMK susijusiais klausimais."
    )


def asks_for_questions_before_choosing(user_message: str) -> bool:
    message = normalize_text(user_message)

    return has_any(message, [
        "kokius klausimus tureciau uzduoti sau",
        "pries renkantis studiju programa",
        "pries renkantis studijas",
        "kokios informacijos tau reiketu is manes",
        "kad galetum pasiulyti tinkamesne",
        "kad galetum pasiulyti tinkamesne studiju krypti",
    ])


def handle_questions_before_choosing(user_message: str) -> dict[str, Any]:
    message = normalize_text(user_message)

    if "kokios informacijos" in message or "is manes" in message:
        reply = (
            "Kad galėčiau pasiūlyti tinkamesnę studijų kryptį, labiausiai padėtų ši informacija:\n\n"
            "- kas Jums labiau patinka: technologijos, kūryba, verslas, komunikacija, teisė, sveikata ar darbas su žmonėmis;\n"
            "- ar norite daugiau praktikos, ar platesnių akademinių studijų;\n"
            "- kuriame mieste norėtumėte studijuoti;\n"
            "- ar svarbiau greičiau pradėti dirbti, ar įgyti platesnį išsilavinimą;\n"
            "- kokio darbo ateityje norėtumėte."
        )
    else:
        reply = (
            "Prieš renkantis studijų programą verta sau užduoti kelis klausimus:\n\n"
            "1. Kokia sritis mane iš tikrųjų domina: technologijos, kūryba, verslas, žmonės ar sveikata?\n"
            "2. Ar noriu daugiau praktinių įgūdžių, ar platesnių studijų?\n"
            "3. Kokio darbo norėčiau po studijų?\n"
            "4. Kuriame mieste norėčiau studijuoti?\n"
            "5. Ar man svarbiau greičiau įgyti kvalifikaciją, ar studijuoti plačiau?\n\n"
            "Atsakius į šiuos klausimus, daug lengviau susiaurinti pasirinkimus."
        )

    return make_response(
        reply,
        [
            {
                "label": "Visos studijų programos",
                "url": STUDIJU_PROGRAMOS_URL,
            }
        ]
    )


def analyze_interest_profile(user_message: str, history: list[dict] | None = None) -> dict[str, Any]:
    message = normalize_text(user_message)
    recent_user_context = get_recent_user_context(history)
    combined_user_text = f"{recent_user_context} {message}"

    profile = {
        "creative": 0,
        "technology": 0,
        "business": 0,
        "people": 0,
        "practical": 0,
        "city_vilnius": False,
        "city_kaunas": False,
        "city_klaipeda": False,
    }

    creative_signals = [
        "dizain",
        "kurti",
        "kurej",
        "kūrėj",
        "kuryb",
        "kūryb",
        "vizual",
        "medij",
        "video",
        "montuoti",
        "animacij",
        "zaidim",
        "žaidim",
        "3d",
        "grafik",
    ]

    technology_signals = [
        "technolog",
        "kompiuter",
        "it",
        "programav",
        "kodas",
        "sistemos",
        "dirbtinis intelektas",
        "di",
        "ai",
        "kibernet",
        "testav",
    ]

    business_signals = [
        "versl",
        "verslav",
        "nuosavo verslo",
        "savo versla",
        "savo verslą",
        "ikurti",
        "įkurti",
        "imone",
        "įmon",
        "marketing",
        "vadyb",
        "pardav",
        "finans",
        "projekt",
    ]

    people_signals = [
        "zmonem",
        "žmonėm",
        "zmonemis",
        "žmonėmis",
        "darbas su zmon",
        "darbas su žmon",
        "bendrauti",
        "bendrav",
        "komunik",
        "padeti zmon",
        "padėti žmon",
        "organizuoti",
        "komanda",
        "klient",
    ]

    practical_signals = [
        "praktik",
        "igudziu",
        "įgūdžių",
        "igudzius",
        "įgūdžius",
        "greiciau",
        "greičiau",
        "kvalifikacij",
        "dirbti",
        "darbo",
        "startuoti",
    ]

    for signal in creative_signals:
        if signal in combined_user_text:
            profile["creative"] += 1

    for signal in technology_signals:
        if signal in combined_user_text:
            profile["technology"] += 1

    for signal in business_signals:
        if signal in combined_user_text:
            profile["business"] += 1

    for signal in people_signals:
        if signal in combined_user_text:
            profile["people"] += 1

    for signal in practical_signals:
        if signal in combined_user_text:
            profile["practical"] += 1

    profile["city_vilnius"] = "vilni" in combined_user_text or "vilnu" in combined_user_text
    profile["city_kaunas"] = "kaun" in combined_user_text
    profile["city_klaipeda"] = "klaiped" in combined_user_text

    return profile


def asks_for_interest_profile_guidance(user_message: str, history: list[dict] | None = None) -> bool:
    message = normalize_text(user_message)
    profile = analyze_interest_profile(user_message, history)

    profile_score = (
        profile["creative"]
        + profile["technology"]
        + profile["business"]
        + profile["people"]
        + profile["practical"]
    )

    explicit_guidance_signals = [
        "ka rinktis",
        "ką rinktis",
        "kokia kryptis",
        "kokios kryptys",
        "kuri kryptis",
        "kurios kryptys",
        "kokia kryptis tiktu",
        "kokia kryptis tiktų",
        "kokios kryptys tiktu",
        "kokios kryptys tiktų",
        "kokios kryptys man tiktu",
        "kokios kryptys man tiktų",
        "labiausiai tiktu",
        "labiausiai tiktų",
        "kas man tiktu",
        "kas man tiktų",
        "kas man labiausiai tiktu",
        "kas man labiausiai tiktų",
        "kas tiktu",
        "kas tiktų",
        "padek apsispresti",
        "padėk apsispręsti",
        "kaip apsispresti",
        "kaip apsispręsti",
        "kaip galeciau apsispresti",
        "kaip galėčiau apsispręsti",
        "nesu tikras",
        "nesu tikra",
        "man patinka",
        "mane domina",
        "noreciau",
        "norėčiau",
        "isivaizduoju save",
        "įsivaizduoju save",
    ]

    followup_guidance_signals = [
        "kokios kryptys",
        "kokia kryptis",
        "labiausiai tiktu",
        "labiausiai tiktų",
        "kas man tiktu",
        "kas man tiktų",
        "kas tiktu",
        "kas tiktų",
        "ka patartum",
        "ką patartum",
    ]

    return (
        profile_score >= 2
        and (
            has_any(message, explicit_guidance_signals)
            or has_any(message, followup_guidance_signals)
        )
    )


def handle_interest_profile_guidance(user_message: str, history: list[dict] | None = None) -> dict[str, Any]:
    profile = analyze_interest_profile(user_message, history)

    strengths = []

    if profile["creative"] > 0:
        strengths.append("kūryba / dizainas")
    if profile["technology"] > 0:
        strengths.append("technologijos")
    if profile["business"] > 0:
        strengths.append("verslas")
    if profile["people"] > 0:
        strengths.append("darbas su žmonėmis")
    if profile["practical"] > 0:
        strengths.append("praktiniai įgūdžiai")

    intro = "Pagal tai, ką parašėte, matau kelias Jums artimas kryptis"
    if strengths:
        intro += f": {', '.join(strengths)}."

    recommendations = []
    links = [
        {
            "label": "Visos studijų programos",
            "url": STUDIJU_PROGRAMOS_URL,
        }
    ]

    if profile["creative"] > 0 and profile["technology"] > 0:
        recommendations.append(
            "„Kompiuteriniai žaidimai ir animacija“ – jei norite jungti kūrybą, vizualus, 3D, animaciją ir technologijas."
        )
        links.insert(0, {
            "label": "Kompiuteriniai žaidimai ir animacija",
            "url": KOMPIUTERINIAI_ZAIDIMAI_URL,
        })

    if profile["technology"] > 0 and profile["creative"] > 0:
        recommendations.append(
            "„Programavimas ir multimedija“ – jei norite daugiau technologijų, bet kartu išlaikyti multimedijos ir kūrybos pusę."
        )
        links.insert(0, {
            "label": "Programavimas ir multimedija",
            "url": PROGRAMAVIMAS_IR_MULTIMEDIJA_URL,
        })
    elif profile["technology"] > 0:
        recommendations.append(
            "„Programavimas ir multimedija“ – jei norite eiti labiau į technologijas, programavimą ir skaitmeninius sprendimus."
        )
        links.insert(0, {
            "label": "Programavimas ir multimedija",
            "url": PROGRAMAVIMAS_IR_MULTIMEDIJA_URL,
        })

    if profile["creative"] > 0 and profile["people"] > 0:
        recommendations.append(
            "Komunikacijos, medijų arba dizaino kryptys – jei norite kurti, bendrauti su žmonėmis ir dirbti kūrybinėje aplinkoje."
        )

    if profile["business"] > 0 and profile["technology"] > 0:
        recommendations.append(
            "„Ateities verslas ir dirbtinis intelektas“ – jei domina verslo, inovacijų ir technologijų derinys."
        )
    elif profile["business"] > 0:
        recommendations.append(
            "Verslo, vadybos arba verslumo kryptys – jei domina nuosavas verslas, projektai, marketingas ar organizavimas."
        )

    if profile["people"] > 0 and profile["business"] == 0 and profile["creative"] == 0:
        recommendations.append(
            "Komunikacijos, turizmo, teisės ar socialiai orientuotos kryptys – jei labiausiai domina darbas su žmonėmis."
        )

    if not recommendations:
        recommendations.append(
            "Pradėčiau nuo visų SMK studijų programų peržiūros ir palyginčiau 2–3 kryptis pagal miestą, kainą, trukmę ir karjeros galimybes."
        )

    city_note = ""
    if profile["city_vilnius"]:
        city_note = "\n\nKadangi minite Vilnių, pirmiausia tikrinkite, kurios iš šių programų vykdomos Vilniuje."
    elif profile["city_kaunas"]:
        city_note = "\n\nKadangi minite Kauną, pirmiausia tikrinkite, kurios iš šių programų vykdomos Kaune."
    elif profile["city_klaipeda"]:
        city_note = "\n\nKadangi minite Klaipėdą, pirmiausia tikrinkite, kurios programos vykdomos Klaipėdoje."

    practical_note = ""
    if profile["practical"] > 0:
        practical_note = (
            "\n\nKadangi Jums svarbūs praktiniai įgūdžiai, lygindami programas atkreipkite dėmesį į praktikos galimybes, "
            "studijų trukmę ir tai, kokiai karjerai programa ruošia."
        )

    reply = (
        f"{intro}\n\n"
        "Pirmiausia siūlyčiau žiūrėti į:\n"
        + "\n".join([f"- {item}" for item in recommendations[:4]])
        + city_note
        + practical_note
        + "\n\n"
        "Geriausias kitas žingsnis: išsirinkite 2–3 programas iš šių krypčių ir palyginkite jų aprašymus, kainą, miestą ir karjeros galimybes."
    )

    unique_links = []
    seen_urls = set()

    for link in links:
        if link["url"] not in seen_urls:
            unique_links.append(link)
            seen_urls.add(link["url"])

    return make_response(reply, unique_links[:3])


def asks_for_business_direction(user_message: str, history: list[dict] | None = None) -> bool:
    message = normalize_text(user_message)
    recent_user_context = get_recent_user_context(history)
    combined_user_text = f"{recent_user_context} {message}"

    clear_business_signals = [
        "versl",
        "verslav",
        "nuosavo verslo",
        "savo versla",
        "savo verslą",
        "ikurti versla",
        "įkurti verslą",
        "imone",
        "įmonę",
        "marketing",
        "vadyb",
        "pardav",
        "finans",
    ]

    preference_signals = [
        "igudziu",
        "įgūdžių",
        "darbo",
        "kvalifikacij",
        "vilniuje",
        "kaune",
        "klaipedoje",
        "greiciau",
        "greičiau",
        "studijuoti",
        "noreciau",
        "norėčiau",
        "domina",
    ]

    creative_or_people_signals = [
        "dizain",
        "kuryb",
        "kūryb",
        "kurej",
        "kūrėj",
        "vizual",
        "medij",
        "zmonem",
        "žmonėm",
        "bendrav",
        "komunik",
    ]

    has_clear_business = has_any(combined_user_text, clear_business_signals)
    has_preference = has_any(message, preference_signals)
    has_creative_or_people = has_any(message, creative_or_people_signals)

    strong_business = has_any(message, [
        "savo versla",
        "savo verslą",
        "nuosavo verslo",
        "ikurti",
        "įkurti",
        "imone",
        "įmon",
        "marketing",
        "vadyb",
        "finans",
    ])

    if has_creative_or_people and not strong_business:
        return False

    return has_clear_business and has_preference


def handle_business_direction_question(user_message: str) -> dict[str, Any]:
    message = normalize_text(user_message)

    city_part = ""
    if "vilni" in message or "vilnu" in message:
        city_part = " Kadangi minite Vilnių, pirmiausia verta tikrinti programas, kurios vykdomos Vilniuje."
    elif "kaun" in message:
        city_part = " Kadangi minite Kauną, pirmiausia verta tikrinti programas, kurios vykdomos Kaune."
    elif "klaiped" in message:
        city_part = " Kadangi minite Klaipėdą, pirmiausia verta tikrinti programas, kurios vykdomos Klaipėdoje."

    reply = (
        "Pagal tai, ką parašėte, Jums labiausiai tiktų verslo, vadybos arba verslumo krypties studijos.\n\n"
        "Jūsų prioritetai:\n"
        "- norite įgyti praktinių įgūdžių;\n"
        "- domina darbas arba nuosavo verslo kūrimas;\n"
        "- svarbu greičiau įgyti aiškią kryptį ar kvalifikaciją.\n\n"
        "Tokiu atveju siūlyčiau peržiūrėti SMK verslo krypties programas. Jei domina modernesnis verslo ir technologijų derinys, verta atkreipti dėmesį ir į „Ateities verslas ir dirbtinis intelektas“ kryptį."
        f"{city_part}\n\n"
        "Geriausias kitas žingsnis:\n"
        "1. Atsidarykite SMK studijų programų sąrašą.\n"
        "2. Palyginkite verslo krypties programas pagal trukmę, kainą, praktikos galimybes ir karjeros kryptį.\n"
        "3. Išsirinkite 2–3 programas, kurios atrodo artimiausios Jūsų tikslui."
    )

    return make_response(
        reply,
        [
            {
                "label": "Visos studijų programos",
                "url": STUDIJU_PROGRAMOS_URL,
            },
            {
                "label": "Stojimas",
                "url": PRIEMIMAS_URL,
            },
        ]
    )


def asks_for_decision_help(user_message: str, history: list[dict] | None = None) -> bool:
    message = normalize_text(user_message)
    context = get_recent_context(history)

    signals = [
        "ka rinktis",
        "ką rinktis",
        "pasiulyk",
        "pasiūlyk",
        "nezinau ka rinktis",
        "nežinau ką rinktis",
        "ka man rinktis",
        "ką man rinktis",
        "ka pasirinkti",
        "ką pasirinkti",
        "kaip galeciau apsispresti",
        "kaip galėčiau apsispręsti",
        "kaip apsispresti",
        "kaip apsispręsti",
        "nesu tikras",
        "nesu tikra",
        "dar nesu tikras",
        "dar nesu tikra",
        "verslas technologijos ar kuryba",
        "verslas technologijos ar kūryba",
    ]

    return has_any(message, signals) or ("pasiulyk" in message and "rinktis" in context)


def handle_decision_help_question() -> dict[str, Any]:
    reply = (
        "Jei dar nesate tikras, ar labiau tinka verslas, technologijos ar kūryba, siūlyčiau apsispręsti per 3 klausimus:\n\n"
        "1. Kas Jums įdomiau kasdienėje veikloje?\n"
        "- kurti, dizainuoti, montuoti, vizualiai galvoti – labiau kūryba;\n"
        "- spręsti logines užduotis ir gilintis į sistemas – labiau technologijos;\n"
        "- organizuoti, parduoti, planuoti ar kurti idėjas verslui – labiau verslas.\n\n"
        "2. Kokio darbo save labiau įsivaizduojate?\n"
        "- kūrėjas / dizaineris / medijų specialistas;\n"
        "- programuotojas / IT specialistas / testuotojas;\n"
        "- vadybininkas / projektų žmogus / verslo kūrėjas.\n\n"
        "3. Ar norite daugiau technikos, kūrybos ar darbo su žmonėmis?\n\n"
        "Pagal tai galima rinktis kryptį: technologijoms – „Programavimas ir multimedija“, kūrybai – žaidimų / dizaino / medijų kryptys, verslui – verslo arba DI taikymo versle kryptys."
    )

    return make_response(
        reply,
        [
            {
                "label": "Visos studijų programos",
                "url": STUDIJU_PROGRAMOS_URL,
            },
            {
                "label": "Programavimas ir multimedija",
                "url": PROGRAMAVIMAS_IR_MULTIMEDIJA_URL,
            },
            {
                "label": "Kompiuteriniai žaidimai ir animacija",
                "url": KOMPIUTERINIAI_ZAIDIMAI_URL,
            },
        ]
    )


def asks_for_broad_tech_without_only_programming(user_message: str) -> bool:
    message = normalize_text(user_message)

    return (
        has_any(message, ["technolog", "kompiuter", "it"])
        and has_any(message, ["nenoriu vien tik programuoti", "ne vien tik programuoti", "ne tik programuoti"])
    )


def handle_broad_tech_without_only_programming() -> dict[str, Any]:
    reply = (
        "Jei domina technologijos, bet nenorite vien tik programuoti, verta žiūrėti į platesnes technologijų ir kūrybinių industrijų kryptis:\n\n"
        "- „Programavimas ir multimedija“ – technologijų, programavimo ir multimedijos derinys.\n"
        "- „Kompiuteriniai žaidimai ir animacija“ – kūryba, žaidimai, 3D, animacija ir vizualiniai sprendimai.\n"
        "- „Ateities verslas ir dirbtinis intelektas“ – technologijų ir DI taikymas versle.\n"
        "- „Informacijos ir kibernetinė sauga“ – IT saugumo kryptis."
    )

    return make_response(
        reply,
        [
            {
                "label": "Visos studijų programos",
                "url": STUDIJU_PROGRAMOS_URL,
            },
            {
                "label": "Programavimas ir multimedija",
                "url": PROGRAMAVIMAS_IR_MULTIMEDIJA_URL,
            },
            {
                "label": "Kompiuteriniai žaidimai ir animacija",
                "url": KOMPIUTERINIAI_ZAIDIMAI_URL,
            },
        ]
    )


def asks_for_creative_tech_direction(user_message: str) -> bool:
    message = normalize_text(user_message)

    return (
        has_any(message, ["patinka kuryba", "patinka kūryba", "dizain", "vizual", "medij", "animacij", "zaidim", "žaidim"])
        and has_any(message, ["kompiuter", "technolog", "studij", "krypt", "tiktu", "galetu tikti"])
        and not has_any(message, ["verslas technologijos ar kuryba", "verslas technologijos ar kūryba", "nesu tikras", "nesu tikra"])
    )


def handle_creative_tech_direction() -> dict[str, Any]:
    reply = (
        "Jei patinka kūryba, dizainas ir kompiuteriai, labiausiai žiūrėčiau į kūrybinių technologijų kryptis:\n\n"
        "- „Kompiuteriniai žaidimai ir animacija“ – žaidimų kūrimas, 3D, animacija ir vizualiniai sprendimai.\n"
        "- „Programavimas ir multimedija“ – daugiau technologijų ir programavimo, bet kartu yra multimedijos dalis.\n"
        "- Dizaino arba medijų kryptys – jei labiau traukia vizualai, kūrybinis turinys ir komunikacija.\n\n"
        "Jei norite daugiau kodo – rinkčiausi „Programavimas ir multimedija“. Jei daugiau kūrybos ir vizualų – „Kompiuteriniai žaidimai ir animacija“ arba dizaino kryptį."
    )

    return make_response(
        reply,
        [
            {
                "label": "Kompiuteriniai žaidimai ir animacija",
                "url": KOMPIUTERINIAI_ZAIDIMAI_URL,
            },
            {
                "label": "Programavimas ir multimedija",
                "url": PROGRAMAVIMAS_IR_MULTIMEDIJA_URL,
            },
            {
                "label": "Visos studijų programos",
                "url": STUDIJU_PROGRAMOS_URL,
            },
        ]
    )


def asks_for_program_comparison(user_message: str) -> bool:
    message = normalize_text(user_message)

    return (
        has_any(message, ["palygink", "palyginti", "kuo skiriasi", "skirtumas"])
        and "programav" in message
        and has_any(message, ["zaidim", "žaidim", "animacij", "kompiuterin"])
    )


def handle_program_comparison() -> dict[str, Any]:
    reply = (
        "Trumpai palyginant:\n\n"
        "- „Programavimas ir multimedija“ labiau tinka, jei norite daugiau programavimo, programinės įrangos kūrimo ir techninių įgūdžių.\n"
        "- „Kompiuteriniai žaidimai ir animacija“ labiau tinka, jei domina kūrybinės technologijos: žaidimų kūrimas, 3D, animacija ir vizualinė medija.\n\n"
        "Jei tikslas – tapti programuotoju, stipresnis pasirinkimas būtų „Programavimas ir multimedija“. Jei norite jungti technologijas su kūryba ir vizualais, verta žiūrėti į „Kompiuterinius žaidimus ir animaciją“."
    )

    return make_response(
        reply,
        [
            {
                "label": "Programavimas ir multimedija",
                "url": PROGRAMAVIMAS_IR_MULTIMEDIJA_URL,
            },
            {
                "label": "Kompiuteriniai žaidimai ir animacija",
                "url": KOMPIUTERINIAI_ZAIDIMAI_URL,
            },
        ]
    )


def asks_for_practical_studies(user_message: str) -> bool:
    message = normalize_text(user_message)

    return has_any(message, [
        "praktine kvalifikacija",
        "praktiniu studiju",
        "ne vien teorijos",
        "ne tik teorijos",
        "greiciau igyti",
        "trumpuju studiju programa butu geras variantas",
    ])


def handle_practical_studies_question() -> dict[str, Any]:
    reply = (
        "Taip, jei norite daugiau praktikos ir mažiau vien teorinio mokymosi, SMK gali būti tinkamas pasirinkimas.\n\n"
        "Jei norite greitesnio praktinio kelio, verta žiūrėti į trumpųjų studijų programas, pavyzdžiui:\n"
        "- „Programavimas“ – programuotojo kvalifikacijai;\n"
        "- „Programinės įrangos testavimas“ – testuotojo kvalifikacijai.\n\n"
        "Jei norite platesnių studijų, verta rinktis bakalauro studijų programą, pavyzdžiui „Programavimas ir multimedija“."
    )

    return make_response(
        reply,
        [
            {
                "label": "Visos studijų programos",
                "url": STUDIJU_PROGRAMOS_URL,
            }
        ]
    )


def asks_for_one_evening_plan(user_message: str) -> bool:
    message = normalize_text(user_message)

    return has_any(message, [
        "per viena vakara",
        "trumpa plana",
        "susidaryti plana",
    ])


def handle_one_evening_plan() -> dict[str, Any]:
    reply = (
        "Per vieną vakarą galima susidaryti aiškų pradinį planą:\n\n"
        "1. 20 min. – užsirašykite, kas Jums patinka: technologijos, kūryba, verslas, žmonės ar sveikata.\n"
        "2. 30–40 min. – peržiūrėkite SMK studijų programas ir pasižymėkite 3–5 dominančias.\n"
        "3. 20 min. – palyginkite jas pagal miestą, kainą, trukmę ir karjeros kryptį.\n"
        "4. 15 min. – užsirašykite klausimus, kuriuos dar reikia išsiaiškinti.\n"
        "5. Pabaigoje pasirinkite 1–2 programas, apie kurias norite sužinoti daugiau."
    )

    return make_response(
        reply,
        [
            {
                "label": "Visos studijų programos",
                "url": STUDIJU_PROGRAMOS_URL,
            }
        ]
    )


def asks_for_kaunas_search(user_message: str) -> bool:
    message = normalize_text(user_message)

    return "kaun" in message and has_any(message, [
        "programu paieska",
        "mokytis kaune",
        "studijuoti kaune",
        "kaune nuo ko pradeti",
    ])


def handle_kaunas_search() -> dict[str, Any]:
    reply = (
        "Jei norite mokytis Kaune, pradėčiau nuo SMK studijų programų puslapio ir tikrinčiau programas pagal miestą.\n\n"
        "Praktiškas kelias:\n"
        "1. Atsidarykite visas studijų programas.\n"
        "2. Peržiūrėkite, kurios programos vykdomos Kaune.\n"
        "3. Išsirinkite 2–3 dominančias programas.\n"
        "4. Palyginkite kainą, trukmę, studijų turinį ir karjeros kryptį."
    )

    return make_response(
        reply,
        [
            {
                "label": "Visos studijų programos",
                "url": STUDIJU_PROGRAMOS_URL,
            }
        ]
    )


def asks_for_other_studies(user_message: str) -> bool:
    message = normalize_text(user_message)

    return has_any(message, [
        "be programav",
        "ne programav",
        "kitos studijos",
        "kitu studiju",
    ])


def handle_other_studies_question() -> dict[str, Any]:
    reply = (
        "Be programavimo krypties SMK turi ir kitų studijų sričių: verslo, komunikacijos, kūrybinių industrijų, teisės, turizmo, sveikatos mokslų ir kitų krypčių.\n\n"
        "Patogiausia rinktis pagal tai, kas Jums artimiausia:\n"
        "- technologijos ir kodas;\n"
        "- kūryba, dizainas ar medijos;\n"
        "- verslas ir vadyba;\n"
        "- darbas su žmonėmis;\n"
        "- sveikatos ar grožio sritis."
    )

    return make_response(
        reply,
        [
            {
                "label": "Visos studijų programos",
                "url": STUDIJU_PROGRAMOS_URL,
            }
        ]
    )


def asks_for_admission(user_message: str) -> bool:
    message = normalize_text(user_message)

    return has_any(message, [
        "kaip istot",
        "kaip istoti",
        "stojimas",
        "stoti",
        "priemimas",
        "po 12 klases",
        "dokumentu reikia",
        "stojimo mokestis",
        "registracijos imoka",
        "noriu stoti",
    ])


def handle_admission_question(user_message: str) -> dict[str, Any]:
    message = normalize_text(user_message)

    if "po 12" in message:
        reply = "Taip, į SMK galima stoti baigus 12 klasių. Daugiau apie priėmimo sąlygas, dokumentus ir terminus rasite SMK stojimo puslapyje."
    elif "dokument" in message:
        reply = "Stojant svarbu pasiruošti reikalingus dokumentus. Tikslų dokumentų sąrašą ir priėmimo eigą rasite SMK stojimo puslapyje."
    elif "mokestis" in message or "imoka" in message:
        reply = "Stojimo registracijos įmoka pagal turimą informaciją yra 70 EUR. Tikslias sąlygas rekomenduoju pasitikrinti SMK stojimo puslapyje."
    else:
        reply = (
            "Į SMK galima stoti internetu per SMK priėmimo sistemą arba kreipiantis į priėmimo komandą. "
            "Stojimo puslapyje rasite priėmimo eigą, terminus ir reikalingus dokumentus."
        )

    return make_response(
        reply,
        [
            {
                "label": "Stojimas",
                "url": PRIEMIMAS_URL,
            }
        ]
    )


def asks_for_contacts(user_message: str) -> bool:
    message = normalize_text(user_message)

    return has_any(message, [
        "kontakt",
        "adresas",
        "telefon",
        "el pastas",
        "email",
        "kur smk",
        "kur yra smk",
        "vilniuje randasi",
        "vilnuje randasi",
        "smk vilniuje",
        "smk vilnuje",
        "smk kaune",
        "smk klaipedoje",
        "priemimo el",
    ])


def handle_contacts_question(user_message: str) -> dict[str, Any]:
    message = normalize_text(user_message)

    try:
        data = load_smk_data()
        contacts = data.get("contacts", {})
        cities = contacts.get("cities", [])
        main_contact_page = contacts.get("main_contact_page", KONTAKTAI_URL)
        general_email = contacts.get("general_email", "")
        admission_email = contacts.get("admission_email", "")

        if "priemimo" in message:
            if admission_email:
                return make_response(
                    f"SMK priėmimo klausimams nurodomas el. paštas: {admission_email}.",
                    [
                        {
                            "label": "Kontaktai",
                            "url": main_contact_page,
                        }
                    ]
                )

            return make_response(
                "Tikslaus priėmimo el. pašto šiuo metu neturiu. Rekomenduoju pasitikrinti SMK kontaktų arba stojimo puslapyje.",
                [
                    {
                        "label": "Kontaktai",
                        "url": main_contact_page,
                    },
                    {
                        "label": "Stojimas",
                        "url": PRIEMIMAS_URL,
                    },
                ]
            )

        city_key = None

        if "vilni" in message or "vilnu" in message:
            city_key = "vilnius"
        elif "kaun" in message:
            city_key = "kaunas"
        elif "klaiped" in message:
            city_key = "klaipeda"

        if city_key:
            for city in cities:
                city_name = normalize_text(city.get("city", ""))

                if city_key in city_name:
                    phones = ", ".join(city.get("phones", [])) if city.get("phones") else "Nenurodyta"
                    emails = ", ".join(city.get("emails", [])) if city.get("emails") else "Nenurodyta"
                    address = city.get("address", "Nenurodyta")
                    url = city.get("url", main_contact_page)

                    return make_response(
                        f"SMK {city.get('city', '').strip()} padalinio informacija:\n"
                        f"- Adresas: {address}\n"
                        f"- Telefonai: {phones}\n"
                        f"- El. paštai: {emails}",
                        [
                            {
                                "label": f"{city.get('city', 'SMK')} kontaktai",
                                "url": url,
                            },
                            {
                                "label": "Visi kontaktai",
                                "url": main_contact_page,
                            },
                        ]
                    )

        if general_email:
            reply = f"SMK bendras kontaktinis el. paštas: {general_email}. Daugiau kontaktų rasite oficialiame kontaktų puslapyje."
        else:
            reply = "SMK kontaktus ir padalinių informaciją patogiausia rasti oficialiame kontaktų puslapyje."

        return make_response(
            reply,
            [
                {
                    "label": "Kontaktai",
                    "url": main_contact_page,
                }
            ]
        )

    except Exception as error:
        print("[CONTACTS ERROR]", repr(error))

        return make_response(
            "SMK kontaktus ir padalinių informaciją patogiausia rasti oficialiame kontaktų puslapyje.",
            [
                {
                    "label": "Kontaktai",
                    "url": KONTAKTAI_URL,
                }
            ]
        )


def asks_for_programming_price_or_link(user_message: str, history: list[dict] | None = None) -> bool:
    message = normalize_text(user_message)
    context = get_recent_context(history)

    program_mentioned = has_any(message + " " + context, [
        "programavimas ir multimedija",
        "programavimo ir multimedijos",
        "programavim ir multimed",
        "programavimo inzinerijos kuryba",
        "programavimo inžinerijos kūryba",
    ])

    price_or_link_mentioned = has_any(message, [
        "kaina",
        "kainuoja",
        "mokestis",
        "eur",
        "link",
        "nuoroda",
        "aprasymas",
        "kiek",
    ])

    return program_mentioned and price_or_link_mentioned


def handle_programming_price_or_link(user_message: str) -> dict[str, Any]:
    message = normalize_text(user_message)

    if "programavimo inzinerijos kuryba" in message or "programavimo inžinerijos kūryba" in message:
        intro = (
            "Tokio tikslaus programos pavadinimo savo turimoje SMK informacijoje nerandu. "
            "Gali būti, kad turėjote omenyje programą „Programavimas ir multimedija“."
        )
    else:
        intro = "Žinoma. „Programavimas ir multimedija“ studijų programa yra viena iš SMK informatikos krypties programų."

    reply = (
        f"{intro}\n\n"
        "Šios programos kaina:\n"
        "- 1675 Eur už semestrą\n"
        "- 3350 Eur už metus\n\n"
        "Programos aprašymą galite atidaryti per žemiau pateiktą nuorodą."
    )

    return make_response(
        reply,
        [
            {
                "label": "Programavimas ir multimedija",
                "url": PROGRAMAVIMAS_IR_MULTIMEDIJA_URL,
            },
            {
                "label": "Visos studijų programos",
                "url": STUDIJU_PROGRAMOS_URL,
            },
        ]
    )


def asks_programming_city_followup(user_message: str, history: list[dict] | None = None) -> bool:
    message = normalize_text(user_message)
    context = get_recent_context(history)

    city_signal = has_any(message, [
        "kaune",
        "kaunas",
        "vilniuje",
        "vilnius",
        "vilnuje",
        "klaipedoje",
        "kur vyksta",
        "kokiam mieste",
        "kokiuose miestuose",
    ])

    program_context = (
        "programavimas ir multimedija" in context
        or "programavimo ir multimedijos" in context
    )

    return city_signal and program_context


def handle_programming_city_followup(user_message: str) -> dict[str, Any]:
    message = normalize_text(user_message)

    if "kaun" in message:
        reply = "Taip, „Programavimas ir multimedija“ programa vykdoma Kaune."
    elif "vilni" in message or "vilnu" in message:
        reply = "Taip, „Programavimas ir multimedija“ programa vykdoma Vilniuje."
    elif "klaiped" in message:
        reply = "Savo turimoje informacijoje matau, kad „Programavimas ir multimedija“ vykdoma Vilniuje ir Kaune. Dėl Klaipėdos rekomenduočiau pasitikrinti programos aprašyme arba susisiekti su SMK."
    else:
        reply = "„Programavimas ir multimedija“ programa vykdoma Vilniuje ir Kaune."

    return make_response(
        reply,
        [
            {
                "label": "Programavimas ir multimedija",
                "url": PROGRAMAVIMAS_IR_MULTIMEDIJA_URL,
            }
        ]
    )


def asks_about_ai_business_program(user_message: str) -> bool:
    message = normalize_text(user_message)

    return (
        "ateities verslas" in message
        and has_any(message, ["dirbtinis intelektas", "di", "ai"])
        and "programav" in message
    )


def handle_ai_business_program_question() -> dict[str, Any]:
    return make_response(
        "Ne, „Ateities verslas ir dirbtinis intelektas“ nėra tiesioginė programavimo programa. Ji labiau orientuota į verslą, inovacijas ir dirbtinio intelekto taikymą organizacijose. Ji gali būti aktuali, jei domina technologijų pritaikymas versle, bet jei norite tapti programuotoju, labiau tiktų „Programavimas ir multimedija“ arba trumpųjų studijų programa „Programavimas“.",
        [
            {
                "label": "Visos studijų programos",
                "url": STUDIJU_PROGRAMOS_URL,
            }
        ]
    )


def asks_for_direct_programming_choice(user_message: str, history: list[dict] | None = None) -> bool:
    message = normalize_text(user_message)
    context = get_recent_context(history)

    direct_signals = [
        "labiausiai tiesiogiai",
        "tiesiogiai susijus",
        "tapti programuotoju",
        "daugiausiai kodo",
        "labiausiai programavimas",
        "noriu buti programuotoju",
        "kuri labiausiai tinka",
        "kurios labiausiai tinka",
    ]

    return (
        has_any(message, direct_signals)
        and ("programav" in message or "programav" in context or "it" in context)
    )


def handle_direct_programming_choice() -> dict[str, Any]:
    reply = (
        "Jei tikslas yra kuo labiau eiti į programavimą, rinkčiausi šias kryptis:\n\n"
        "1. „Programavimas ir multimedija“ – geriausias pasirinkimas, jei norite platesnių studijų su programavimu, programinės įrangos kūrimu ir skaitmeninėmis technologijomis.\n"
        "2. Trumpųjų studijų programa „Programavimas“ – tinkama, jei norite greičiau įgyti programuotojo kvalifikaciją.\n"
        "3. „Programinės įrangos testavimas“ – labiau tinka, jei domina programų kokybės tikrinimas, testavimas ir klaidų analizė."
    )

    return make_response(
        reply,
        [
            {
                "label": "Programavimas ir multimedija",
                "url": PROGRAMAVIMAS_IR_MULTIMEDIJA_URL,
            },
            {
                "label": "Visos studijų programos",
                "url": STUDIJU_PROGRAMOS_URL,
            },
        ]
    )


def asks_for_programming_studies(user_message: str) -> bool:
    message = normalize_text(user_message)

    if not has_any(message, ["programav", "it", "informatik", "technolog"]):
        return False

    signals = [
        "visas",
        "isvardink",
        "kokiu",
        "pasirinkim",
        "daugiau",
        "susije",
        "susijus",
        "programu",
        "studiju",
        "noriu suzinoti",
        "studijuoti kazka su technologij",
    ]

    return has_any(message, signals)


def handle_programming_studies_question() -> dict[str, Any]:
    reply = (
        "Su programavimu ir IT sritimi SMK labiausiai susijusios šios kryptys:\n\n"
        "Tiesiogiai su programavimu:\n"
        "- „Programavimas ir multimedija“ – programavimas, programinės įrangos kūrimas ir skaitmeninės technologijos.\n"
        "- Trumpųjų studijų programa „Programavimas“ – trumpesnė programa, orientuota į programuotojo kvalifikaciją.\n\n"
        "Artimos IT kryptys:\n"
        "- „Programinės įrangos testavimas“ – programų testavimas ir kokybės užtikrinimas.\n"
        "- „Informacijos ir kibernetinė sauga“ – IT sauga ir kibernetinis saugumas.\n"
        "- „Kompiuteriniai žaidimai ir animacija“ – kūrybinės technologijos, žaidimų kūrimas, 3D ir animacija.\n\n"
        "Svarbu: „Ateities verslas ir dirbtinis intelektas“ nėra tiesioginė programavimo programa, bet gali būti aktuali, jei domina DI taikymas versle ir technologijose."
    )

    return make_response(
        reply,
        [
            {
                "label": "Programavimas ir multimedija",
                "url": PROGRAMAVIMAS_IR_MULTIMEDIJA_URL,
            },
            {
                "label": "Kompiuteriniai žaidimai ir animacija",
                "url": KOMPIUTERINIAI_ZAIDIMAI_URL,
            },
            {
                "label": "Visos studijų programos",
                "url": STUDIJU_PROGRAMOS_URL,
            },
        ]
    )


def asks_for_student_systems(user_message: str, history: list[dict] | None = None) -> bool:
    message = normalize_text(user_message)
    context = get_recent_context(history)

    direct_signals = [
        "moodle",
        "classter",
        "tvarkarast",
        "tvarkarašt",
        "uzduotis",
        "uzduotys",
        "pazym",
        "pažym",
        "studentu sistema",
        "studentų sistema",
        "savitarnos sistema",
        "prisijungti prie moodle",
        "prisijungti prie classter",
        "studentai mato tvarkarasti",
    ]

    if has_any(message, direct_signals):
        return True

    if has_any(context, ["moodle", "classter", "tvarkarast", "uzduotis", "studentu sistema"]):
        followup_signals = ["svetaine", "puslap", "kur", "kokia", "prisijung", "pazym", "uzduotis"]
        return has_any(message, followup_signals)

    return False


def handle_student_systems_question(user_message: str) -> dict[str, Any]:
    message = normalize_text(user_message)

    asks_both = (
        ("moodle" in message and "classter" in message)
        or (has_any(message, ["tvarkarast", "tvarkarašt"]) and has_any(message, ["uzduot"]))
        or "kuo skiriasi moodle ir classter" in message
    )

    if asks_both:
        reply = (
            "SMK studentai dažniausiai naudoja dvi pagrindines sistemas:\n\n"
            "- „Classter“ – tvarkaraščiams, pažymiams ir akademinei informacijai.\n"
            "- „Moodle“ – mokymosi medžiagai, užduotims ir kursų informacijai.\n\n"
            "Trumpai: Classter labiau skirtas administracinei studijų informacijai, o Moodle – mokymuisi ir užduotims."
        )

        return make_response(
            reply,
            [
                {
                    "label": "Classter",
                    "url": CLASSTER_URL,
                },
                {
                    "label": "Moodle",
                    "url": MOODLE_URL,
                },
                {
                    "label": "Studentams",
                    "url": STUDENTAMS_URL,
                },
            ]
        )

    if has_any(message, ["pamirs", "pamirsc", "pamirš", "prisijungima", "prisijungimą", "slaptazod"]):
        return make_response(
            "Jei pamirštumėte prisijungimą prie studentų sistemos, pirmiausia reikėtų kreiptis į SMK studentų informacijos / administracijos kontaktus arba naudoti prisijungimo atkūrimo galimybę pačioje sistemoje, jei ji pateikta.",
            [
                {
                    "label": "Studentams",
                    "url": STUDENTAMS_URL,
                },
                {
                    "label": "Kontaktai",
                    "url": KONTAKTAI_URL,
                },
            ]
        )

    if "moodle" in message or has_any(message, ["uzduotis", "uzduotys", "mokymosi medziaga"]):
        return make_response(
            "Užduotims, mokymosi medžiagai ir kursų informacijai SMK studentai naudoja „Moodle“ virtualią mokymosi aplinką.",
            [
                {
                    "label": "Moodle",
                    "url": MOODLE_URL,
                }
            ]
        )

    if "classter" in message or has_any(message, ["tvarkarast", "tvarkarašt", "pazym", "pažym"]):
        return make_response(
            "Tvarkaraščiams, pažymiams ir akademinei informacijai SMK studentai naudoja „Classter“ studentų savitarnos sistemą.",
            [
                {
                    "label": "Classter",
                    "url": CLASSTER_URL,
                }
            ]
        )

    reply = (
        "SMK studentai dažniausiai naudoja dvi pagrindines sistemas:\n\n"
        "- „Classter“ – tvarkaraščiams, pažymiams ir akademinei informacijai.\n"
        "- „Moodle“ – mokymosi medžiagai, užduotims ir kursų informacijai."
    )

    return make_response(
        reply,
        [
            {
                "label": "Classter",
                "url": CLASSTER_URL,
            },
            {
                "label": "Moodle",
                "url": MOODLE_URL,
            },
        ]
    )


def asks_about_dorms(user_message: str) -> bool:
    message = normalize_text(user_message)

    return has_any(message, [
        "barak",
        "bendrabut",
        "bendrabuc",
        "bendrabuč",
        "apgyvend",
        "kur gyvena studentai",
    ])


def handle_dorms_question() -> dict[str, Any]:
    return make_response(
        "Šiuo metu neturiu tikslios informacijos, ar SMK turi savo bendrabučius ir kokios yra apgyvendinimo sąlygos. Dėl tokios informacijos geriausia kreiptis į SMK kontaktus arba priėmimo skyrių.",
        [
            {
                "label": "Kontaktai",
                "url": KONTAKTAI_URL,
            },
            {
                "label": "Stojimas",
                "url": PRIEMIMAS_URL,
            },
        ]
    )


def should_use_consultant(user_message: str, history: list[dict] | None = None) -> bool:
    message = normalize_text(user_message)

    consultant_signals = [
        "patark",
        "ka patartum",
        "ką patartum",
        "padek apsispresti",
        "padėk apsispręsti",
        "ka rekomenduotum",
        "ką rekomenduotum",
        "noriu bet",
        "man patinka",
        "mane domina",
        "galvoju apie",
        "nezinau",
        "nežinau",
        "esu pasimetes",
        "esu pasimetęs",
        "kaip pasirinkti",
        "kaip apsispresti",
        "kaip apsispręsti",
        "kokia kryptis tiktu",
        "kokia kryptis tiktų",
        "kokios kryptys tiktu",
        "kokios kryptys tiktų",
        "kokios kryptys man labiausiai tiktu",
        "kokios kryptys man labiausiai tiktų",
        "labiausiai tiktu",
        "labiausiai tiktų",
        "kas man tiktu",
        "kas man tiktų",
        "galetum pasiulyti",
        "galėtum pasiūlyti",
    ]

    return has_any(message, consultant_signals)


def build_consultant_context() -> str:
    return (
        "SMK asistentas padeda su studijų programomis, stojimu, kainomis, kontaktais, Moodle ir Classter.\n"
        "Žinomi faktai:\n"
        "- „Programavimas ir multimedija“: 1675 Eur už semestrą, 3350 Eur už metus, vykdoma Vilniuje ir Kaune.\n"
        "- Moodle naudojamas mokymosi medžiagai, užduotims ir kursų informacijai.\n"
        "- Classter naudojamas tvarkaraščiams, pažymiams ir akademinei informacijai.\n"
        "- „Ateities verslas ir dirbtinis intelektas“ nėra tiesioginė programavimo programa, bet susijusi su verslu, inovacijomis ir DI taikymu.\n"
        "- Jei tikslios informacijos nėra, reikia tai pasakyti ir pasiūlyti tikrinti SMK puslapį."
    )


def select_consultant_links(user_message: str) -> list[dict]:
    message = normalize_text(user_message)
    links = []

    def add(label: str, url: str):
        if not any(item["url"] == url for item in links):
            links.append({"label": label, "url": url})

    if has_any(message, ["programavimas ir multimedija", "programavimo ir multimedijos"]):
        add("Programavimas ir multimedija", PROGRAMAVIMAS_IR_MULTIMEDIJA_URL)

    if has_any(message, ["zaidim", "žaidim", "animacij"]):
        add("Kompiuteriniai žaidimai ir animacija", KOMPIUTERINIAI_ZAIDIMAI_URL)

    if has_any(message, ["moodle"]):
        add("Moodle", MOODLE_URL)

    if has_any(message, ["classter", "tvarkarast", "pažym", "pazym"]):
        add("Classter", CLASSTER_URL)

    if has_any(message, ["stoj", "priem", "priėm"]):
        add("Stojimas", PRIEMIMAS_URL)

    if has_any(message, ["kontakt", "adresas", "telefon"]):
        add("Kontaktai", KONTAKTAI_URL)

    if not links and has_any(message, ["studij", "program", "versl", "technolog", "kuryb", "kūryb", "krypt"]):
        add("Visos studijų programos", STUDIJU_PROGRAMOS_URL)

    return links[:3]


def answer_with_consultant(user_message: str, history: list[dict] | None = None) -> dict[str, Any] | None:
    try:
        generator = ConsultantGenerator()

        reply = generator.generate(
            user_message=user_message,
            history=history or [],
            smk_context=build_consultant_context(),
            retrieved_context=[],
        )

        return make_response(
            reply,
            select_consultant_links(user_message)
        )

    except Exception as error:
        print("[CONSULTANT ERROR]", repr(error))
        return None


def fallback_answer(user_message: str) -> dict[str, Any]:
    try:
        legacy_result = legacy_generate_answer(user_message)

        if legacy_result and legacy_result.get("reply"):
            return legacy_result

    except Exception as error:
        print("[LEGACY FALLBACK ERROR]", repr(error))

    return make_response(
        "Šiuo metu neradau tikslaus atsakymo. Galite patikslinti, ar klausiate apie studijų programą, kainą, stojimą, kontaktus ar studentų sistemas?",
        [
            {
                "label": "Visos studijų programos",
                "url": STUDIJU_PROGRAMOS_URL,
            }
        ]
    )


def generate_answer(user_message: str, history: list[dict] | None = None) -> dict[str, Any]:
    history = history or []

    if asks_for_confidential_file(user_message):
        return handle_confidential_request()

    unsafe_result = try_handle_unsafe(user_message)
    if unsafe_result is not None:
        return unsafe_result

    low_value_result = try_block_low_value_message(user_message)
    if low_value_result is not None:
        return low_value_result

    utility_result = try_handle_utility(user_message, history)
    if utility_result is not None:
        return utility_result

    if asks_out_of_scope_question(user_message):
        return handle_out_of_scope_question()

    if asks_for_questions_before_choosing(user_message):
        return handle_questions_before_choosing(user_message)

    if asks_for_interest_profile_guidance(user_message, history):
        return handle_interest_profile_guidance(user_message, history)

    if asks_for_business_direction(user_message, history):
        return handle_business_direction_question(user_message)

    if asks_for_broad_tech_without_only_programming(user_message):
        return handle_broad_tech_without_only_programming()

    if asks_for_program_comparison(user_message):
        return handle_program_comparison()

    if asks_for_creative_tech_direction(user_message):
        return handle_creative_tech_direction()

    if asks_for_practical_studies(user_message):
        return handle_practical_studies_question()

    if asks_for_decision_help(user_message, history):
        return handle_decision_help_question()

    if asks_for_one_evening_plan(user_message):
        return handle_one_evening_plan()

    if asks_for_kaunas_search(user_message):
        return handle_kaunas_search()

    if asks_for_other_studies(user_message):
        return handle_other_studies_question()

    if asks_for_admission(user_message):
        return handle_admission_question(user_message)

    if asks_for_contacts(user_message):
        return handle_contacts_question(user_message)

    if asks_for_programming_price_or_link(user_message, history):
        return handle_programming_price_or_link(user_message)

    if asks_programming_city_followup(user_message, history):
        return handle_programming_city_followup(user_message)

    if asks_about_ai_business_program(user_message):
        return handle_ai_business_program_question()

    if asks_for_direct_programming_choice(user_message, history):
        return handle_direct_programming_choice()

    if asks_for_programming_studies(user_message):
        return handle_programming_studies_question()

    if asks_for_student_systems(user_message, history):
        return handle_student_systems_question(user_message)

    if asks_about_dorms(user_message):
        return handle_dorms_question()

    if should_use_consultant(user_message, history):
        consultant_result = answer_with_consultant(user_message, history)

        if consultant_result is not None:
            return consultant_result

    try:
        intent = classify_message(user_message, history)
    except Exception:
        intent = "smk"

    if intent in {"smk", "general"}:
        return fallback_answer(user_message)

    return fallback_answer(user_message)