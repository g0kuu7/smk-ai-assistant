from backend.data_loader import load_smk_data
from backend.utils import normalize_text


def make_response(reply: str, links: list | None = None) -> dict:
    return {
        "reply": reply,
        "links": links or []
    }
def contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def generate_answer(user_message: str) -> dict:
    data = load_smk_data()
    message = normalize_text(user_message)

    # 1. Stojimas / priėmimas
    if contains_any(message, [
        "stoj", "stoti", "stojim",
        "priem", "priemim",
        "reikalav", "dokument", "termin", "registracij"
    ]):
        return get_admission_answer(data)

    # 2. Trumpųjų studijų klausimai
    if (
            "trump" in message and "stud" in message
)       or contains_any(message, [
            "trumposios",
            "trumpasias",
            "trumpuju",
            "trumpuju studiju",
            "trumpasis",
            "trumpaji",
            "trumpas ciklas",
            "trumpasis ciklas"
    ]):
        return get_short_cycle_answer(data, message)

    # 3. Profesinis mokymas
    if contains_any(message, [
        "profesinis", "profesinio", "profesini", "mokymas", "mokymo", "mokima"
    ]):
        return get_professional_training_answer(data, message)

    # 4. Kainos
    if contains_any(message, [
        "kaina", "kainuoja", "kainos", "mokestis", "eur", "euro"
    ]):
        return get_price_answer(data, message)

    # 5. Kontaktai
    if contains_any(message, [
        "kontakt", "telefon", "el. pa", "email", "past", "adresas", "susisiekti"
    ]):
        return get_contacts_answer(data, message)

    # 6. Studentų sistemos / resursai
    if contains_any(message, [
        "moodle", "classter", "biblioteka", "erasmus", "stipend", "karjera", "student"
    ]):
        return get_student_resource_answer(data, message)

    # 7. Angliškos programos
    if contains_any(message, [
        "english", "anglu", "anglisk", "international", "study programmes"
    ]):
        return get_english_programmes_answer(data)

    # 8. Studijų programos
    if contains_any(message, [
        "program", "studij", "kurs", "mokytis"
    ]):
        return get_programs_answer(data, message)

    # 9. FAQ
    faq_answer = get_faq_answer(data, message)
    if faq_answer:
        return faq_answer

    return make_response(
        "Atsiprašau, šiuo metu neradau tikslaus atsakymo į tavo klausimą. "
        "Gali paklausti apie studijų programas, kainas, stojimą, kontaktus, "
        "studentų sistemas, trumpąsias studijas ar profesinį mokymą."
    )


def get_contacts_answer(data: dict, message: str) -> dict:
    contacts = data.get("contacts", {})
    city_entries = contacts.get("cities", [])
    main_contact_page = contacts.get("main_contact_page", "https://smk.lt/kontaktai/")
    general_email = contacts.get("general_email", "Nenurodyta")
    admission_email = contacts.get("admission_email", "Nenurodyta")

    for city in city_entries:
        city_name = normalize_text(city.get("city", ""))
        if city_name and city_name in message:
            phones = ", ".join(city.get("phones", [])) if city.get("phones") else "Nenurodyta"
            emails = ", ".join(city.get("emails", [])) if city.get("emails") else "Nenurodyta"
            address = city.get("address", "Nenurodyta")
            url = city.get("url", main_contact_page)

            return make_response(
                f"{city.get('city', 'Šio miesto')} padalinio kontaktai:\n"
                f"- Adresas: {address}\n"
                f"- Telefonai: {phones}\n"
                f"- El. paštai: {emails}",
                links=[
                    {
                        "label": f"Atidaryti {city.get('city', 'miesto')} puslapį",
                        "url": url
                    },
                    {
                        "label": "Atidaryti kontaktų puslapį",
                        "url": main_contact_page
                    }
                ]
            )

    return make_response(
        f"SMK kontaktinė informacija:\n"
        f"- Bendras el. paštas: {general_email}\n"
        f"- Priėmimo el. paštas: {admission_email}\n"
        f"Daugiau kontaktų ir padalinių informaciją rasi oficialiame kontaktų puslapyje.",
        links=[
            {
                "label": "Atidaryti kontaktų puslapį",
                "url": main_contact_page
            }
        ]
    )


def get_admission_answer(data: dict) -> dict:
    admission = data.get("admission", {})

    summary = admission.get("summary", "")
    registration_fee = admission.get("registration_fee", "Nenurodyta")
    separate = admission.get("separate_admission_period", {})
    main_url = admission.get("main_url", "https://smk.lt/stojimas/")
    admission_info_url = admission.get("admission_info_url", "https://smk.lt/priemimas/")

    reply = (
        f"Norint stoti į SMK, svarbu sekti priėmimo terminus ir pasiruošti reikalingus dokumentus. "
        f"Registracijos įmoka yra {registration_fee}, o atskirasis priėmimas vyksta nuo "
        f"{separate.get('start', 'Nenurodyta')} iki {separate.get('end', 'Nenurodyta')}. "
        f"{summary}"
    )

    return make_response(
        reply,
        links=[
            {
                "label": "Atidaryti stojimo puslapį",
                "url": main_url
            },
            {
                "label": "Atidaryti priėmimo informaciją",
                "url": admission_info_url
            }
        ]
    )


def get_programs_answer(data: dict, message: str) -> dict:
    programs = data.get("programs", [])
    matched_programs = find_matching_items(programs, message)

    if matched_programs:
        program = matched_programs[0]
        cities = ", ".join(program.get("city_options", [])) if program.get("city_options") else "Nenurodyta"
        url = program.get("url", "https://smk.lt/studiju-programos/")

        return make_response(
            f"SMK siūlo studijų programą „{program.get('name', 'Nenurodyta')}“. "
            f"{program.get('description', 'Aprašymo nėra')} "
            f"Šią programą galima studijuoti šiuose miestuose: {cities}.",
            links=[
                {
                    "label": "Atidaryti programos puslapį",
                    "url": url
                },
                {
                    "label": "Atidaryti visas studijų programas",
                    "url": "https://smk.lt/studiju-programos/"
                }
            ]
        )

    return make_response(
        "Visas SMK studijų programas gali rasti oficialiame studijų programų puslapyje.",
        links=[
            {
                "label": "Atidaryti studijų programas",
                "url": "https://smk.lt/studiju-programos/"
            }
        ]
    )


def get_price_answer(data: dict, message: str) -> dict:
    prices_lt = data.get("study_prices_lt", [])
    prices_en = data.get("study_prices_en", [])
    short_cycle = data.get("short_cycle_programs", [])
    professional = data.get("professional_training", {}).get("programs", [])
    programs = data.get("programs", [])

    matched_lt = find_matching_items(prices_lt, message)
    if matched_lt:
        item = matched_lt[0]
        program_url = find_program_url(programs, item.get("name", ""))

        return make_response(
            f"Studijų programos „{item.get('name', 'Nenurodyta')}“ kaina yra "
            f"{item.get('semester_price', 'Nenurodyta')} už semestrą ir "
            f"{item.get('year_price', 'Nenurodyta')} už metus.",
            links=build_program_links(program_url)
        )

    matched_en = find_matching_items(prices_en, message)
    if matched_en:
        item = matched_en[0]
        program_url = find_program_url(programs, item.get("name", ""))

        return make_response(
            f"Anglų kalba dėstomos programos „{item.get('name', 'Nenurodyta')}“ kaina yra "
            f"{item.get('semester_price', 'Nenurodyta')} už semestrą ir "
            f"{item.get('year_price', 'Nenurodyta')} už metus.",
            links=build_program_links(program_url)
        )

    matched_short = find_matching_items(short_cycle, message)
    if matched_short:
        item = matched_short[0]
        return make_response(
            f"Trumposios studijų programos „{item.get('name', 'Nenurodyta')}“ kaina yra "
            f"{item.get('semester_price', 'Nenurodyta')} už semestrą ir "
            f"{item.get('year_price', 'Nenurodyta')} už metus.",
            links=[
                {
                    "label": "Atidaryti priėmimo puslapį",
                    "url": "https://smk.lt/priemimas/"
                }
            ]
        )

    matched_prof = find_matching_items(professional, message)
    if matched_prof:
        item = matched_prof[0]
        return make_response(
            f"Profesinio mokymo programos „{item.get('name', 'Nenurodyta')}“ kaina yra "
            f"{item.get('primary_price', 'Nenurodyta')} pirminiam mokymui ir "
            f"{item.get('continuing_price', 'Nenurodyta')} tęstiniam mokymui.",
            links=[
                {
                    "label": "Atidaryti priėmimo puslapį",
                    "url": "https://smk.lt/priemimas/"
                }
            ]
        )

    return make_response(
        "Tikslios kainos pagal šį klausimą neradau. Pabandyk paklausti konkrečios programos, pavyzdžiui: „Kiek kainuoja Programavimas ir multimedija?“",
        links=[
            {
                "label": "Atidaryti studijų programas",
                "url": "https://smk.lt/studiju-programos/"
            }
        ]
    )


def get_student_resource_answer(data: dict, message: str) -> dict:
    resources = data.get("student_resources", [])
    matched = find_matching_items(resources, message)

    if matched:
        item = matched[0]
        name = item.get("name", "resursą")
        url = item.get("url", "https://smk.lt/studentams/")

        if normalize_text(name) == "moodle":
            reply = (
                "Prisijungti prie Moodle gali per oficialią SMK virtualią mokymosi sistemą. "
                "Ten rasi studijų medžiagą, užduotis, testus ir kitą su kursais susijusią informaciją."
            )
        elif normalize_text(name) == "classter":
            reply = (
                "Prisijungti prie Classter gali per oficialią SMK studentų sistemą. "
                "Joje matysi pažymius, tvarkaraščius ir kitą svarbią akademinę informaciją."
            )
        else:
            reply = (
                f"Radau tau tinkamą SMK resursą – „{name}“. "
                f"{item.get('description', 'Čia rasi daugiau susijusios informacijos.')}"
            )

        return make_response(
            reply,
            links=[
                {
                    "label": f"Atidaryti {name}",
                    "url": url
                }
            ]
        )

    return make_response(
        "Pagrindinius studentų resursus gali rasti studentams skirtame puslapyje.",
        links=[
            {
                "label": "Atidaryti studentų puslapį",
                "url": "https://smk.lt/studentams/"
            }
        ]
    )


def get_short_cycle_answer(data: dict, message: str) -> dict:
    programs = data.get("short_cycle_programs", [])

    matched = find_matching_items(programs, message)
    if matched:
        item = matched[0]
        cities = ", ".join(item.get("city_options", [])) if item.get("city_options") else "Nenurodyta"
        return make_response(
            f"SMK siūlo trumpųjų studijų programą „{item.get('name', 'Nenurodyta')}“. "
            f"Įgyjama kvalifikacija: {item.get('qualification', 'Nenurodyta')}. "
            f"Studijų trukmė – {item.get('duration_nl', 'Nenurodyta')}, "
            f"studijos vyksta šiuose miestuose: {cities}, "
            f"o kaina metams yra {item.get('year_price', 'Nenurodyta')}.",
            links=[
                {
                    "label": "Atidaryti priėmimo puslapį",
                    "url": "https://smk.lt/priemimas/"
                }
            ]
        )

    if not programs:
        return make_response("Trumposios studijų programų informacijos neradau.")

    lines = ["Taip, SMK vykdo trumpąsias studijas. Šiuo metu siūlomos tokios programos:"]
    for item in programs:
        lines.append(
            f"- {item.get('name', 'Nenurodyta')} – "
            f"{item.get('duration_nl', 'Nenurodyta')}, "
            f"{item.get('year_price', 'Nenurodyta')} per metus"
        )

    return make_response(
        "\n".join(lines),
        links=[
            {
                "label": "Atidaryti priėmimo puslapį",
                "url": "https://smk.lt/priemimas/"
            }
        ]
    )


def get_professional_training_answer(data: dict, message: str) -> dict:
    prof = data.get("professional_training", {})
    programs = prof.get("programs", [])

    matched = find_matching_items(programs, message)
    if matched:
        item = matched[0]
        return make_response(
            f"SMK vykdo profesinio mokymo programą „{item.get('name', 'Nenurodyta')}“. "
            f"Pirminio mokymo kaina yra {item.get('primary_price', 'Nenurodyta')} "
            f"({item.get('primary_duration', 'Nenurodyta')}), o tęstinio mokymo kaina – "
            f"{item.get('continuing_price', 'Nenurodyta')} "
            f"({item.get('continuing_duration', 'Nenurodyta')}).",
            links=[
                {
                    "label": "Atidaryti priėmimo puslapį",
                    "url": "https://smk.lt/priemimas/"
                }
            ]
        )

    if not programs:
        return make_response("Profesinio mokymo informacijos neradau.")

    lines = ["Taip, SMK vykdo profesinį mokymą. Tarp siūlomų programų yra:"]
    for item in programs[:8]:
        lines.append(
            f"- {item.get('name', 'Nenurodyta')} "
            f"(pirminis – {item.get('primary_price', 'Nenurodyta')}, "
            f"tęstinis – {item.get('continuing_price', 'Nenurodyta')})"
        )

    return make_response(
        "\n".join(lines),
        links=[
            {
                "label": "Atidaryti priėmimo puslapį",
                "url": "https://smk.lt/priemimas/"
            }
        ]
    )


def get_english_programmes_answer(data: dict) -> dict:
    programmes = data.get("english_programmes", [])

    if not programmes:
        return make_response("Angliškų studijų programų informacijos neradau.")

    lines = ["SMK siūlo ir studijų programas anglų kalba. Tarp jų yra:"]
    for item in programmes:
        lines.append(
            f"- {item.get('name', 'Nenurodyta')}: {item.get('description', 'Aprašymo nėra')}"
        )

    return make_response(
        "\n".join(lines),
        links=[
            {
                "label": "Atidaryti English study programmes",
                "url": "https://smk.lt/en/study-programmes/"
            }
        ]
    )


def get_faq_answer(data: dict, message: str) -> dict | None:
    faq_items = data.get("faq", [])
    message_words = [word for word in message.split() if len(word) > 3]

    best_match = None
    best_score = 0

    for item in faq_items:
        question = normalize_text(item.get("question", ""))
        answer = item.get("answer", "")
        url = item.get("url", "")

        if not question or not answer:
            continue

        question_words = [word for word in question.split() if len(word) > 3]
        overlap = [word for word in question_words if word in message_words]
        score = len(overlap)

        if score > best_score:
            best_score = score
            best_match = {
                "answer": answer,
                "url": url
            }

    if best_match and best_score >= 2:
        links = []
        if best_match.get("url"):
            links.append({
                "label": "Atidaryti susijusį puslapį",
                "url": best_match["url"]
            })
        return make_response(best_match["answer"], links=links)

    return None


def find_matching_items(items: list, message: str) -> list:
    message_words = [word for word in message.split() if len(word) > 2]
    matched = []

    for item in items:
        name = normalize_text(item.get("name", ""))
        description = normalize_text(item.get("description", ""))

        score = 0

        if name and name in message:
            score += 12

        for word in message_words:
            if word in name:
                score += 3
            if description and word in description:
                score += 1

        if score > 0:
            matched.append((score, item))

    matched.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in matched]


def find_program_url(programs: list, name: str) -> str | None:
    normalized_name = normalize_text(name)

    for program in programs:
        if normalize_text(program.get("name", "")) == normalized_name:
            return program.get("url")

    return None


def build_program_links(program_url: str | None) -> list:
    links = []

    if program_url:
        links.append({
            "label": "Atidaryti programos puslapį",
            "url": program_url
        })

    links.append({
        "label": "Atidaryti visas studijų programas",
        "url": "https://smk.lt/studiju-programos/"
    })

    return links