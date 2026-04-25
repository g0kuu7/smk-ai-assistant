from rag.schemas import Document
from rag.helpers import slugify
from pathlib import Path
from rag.pdf_loader import load_pdf_documents
from rag.chunker import chunk_text


def build_documents(data: dict) -> list[Document]:
    documents: list[Document] = []

    documents.extend(build_general_documents(data))
    documents.extend(build_program_documents(data))
    documents.extend(build_price_documents(data))
    documents.extend(build_contact_documents(data))
    documents.extend(build_admission_documents(data))
    documents.extend(build_short_cycle_documents(data))
    documents.extend(build_professional_training_documents(data))
    documents.extend(build_student_resource_documents(data))
    documents.extend(build_faq_documents(data))
    documents.extend(build_pdf_documents())

    return documents


def build_general_documents(data: dict) -> list[Document]:
    docs = []
    general = data.get("general_info", {})

    if general:
        docs.append(
            Document(
                id="general_info",
                text=(
                    f"{general.get('name', 'SMK')} yra aukštoji mokykla Lietuvoje. "
                    f"{general.get('description', '')} "
                    f"Įkurta {general.get('founded', 'nenurodyta')} metais. "
                    f"Studijos vykdomos šiuose miestuose: {', '.join(general.get('cities', []))}. "
                    f"Pagrindinės studijų kryptys: {', '.join(general.get('study_fields', []))}."
                ),
                metadata={
                    "category": "general",
                    "url": general.get("website", "https://smk.lt/"),
                    "link_label": "Atidaryti SMK puslapį",
                    "name": general.get("name", "SMK")
                }
            )
        )

    return docs


def build_program_documents(data: dict) -> list[Document]:
    docs = []
    programs = data.get("programs", [])
    prices_lt = {item["name"]: item for item in data.get("study_prices_lt", [])}

    for program in programs:
        name = program.get("name", "Nenurodyta")
        cities = ", ".join(program.get("city_options", [])) or "Nenurodyta"
        price = prices_lt.get(name)

        price_text = ""
        if price:
            price_text = (
                f" Programos kaina yra {price.get('semester_price', 'Nenurodyta')} už semestrą "
                f"ir {price.get('year_price', 'Nenurodyta')} už metus."
            )

        docs.append(
            Document(
                id=f"program_{slugify(name)}",
                text=(
                    f"Studijų programa {name}. "
                    f"{program.get('description', '')} "
                    f"Studijų kryptis: {program.get('field', 'Nenurodyta')}. "
                    f"Kalba: {program.get('language', 'Nenurodyta')}. "
                    f"Studijos vykdomos miestuose: {cities}."
                    f"{price_text}"
                ),
                metadata={
                    "category": "program",
                    "name": name,
                    "url": program.get("url", "https://smk.lt/studiju-programos/"),
                    "link_label": f"Atidaryti programą: {name}",
                    "cities": program.get("city_options", []),
                    "language": program.get("language", "LT")
                }
            )
        )

    return docs


def build_price_documents(data: dict) -> list[Document]:
    docs = []

    for item in data.get("study_prices_lt", []):
        name = item.get("name", "Nenurodyta")
        docs.append(
            Document(
                id=f"price_lt_{slugify(name)}",
                text=(
                    f"Studijų programos {name} kaina lietuvių kalba yra "
                    f"{item.get('semester_price', 'Nenurodyta')} už semestrą ir "
                    f"{item.get('year_price', 'Nenurodyta')} už metus."
                ),
                metadata={
                    "category": "price",
                    "name": name,
                    "url": "https://smk.lt/studiju-programos/",
                    "link_label": "Atidaryti studijų programas",
                    "language": "LT"
                }
            )
        )

    for item in data.get("study_prices_en", []):
        name = item.get("name", "Nenurodyta")
        docs.append(
            Document(
                id=f"price_en_{slugify(name)}",
                text=(
                    f"Anglų kalba dėstomos programos {name} kaina yra "
                    f"{item.get('semester_price', 'Nenurodyta')} už semestrą ir "
                    f"{item.get('year_price', 'Nenurodyta')} už metus."
                ),
                metadata={
                    "category": "price",
                    "name": name,
                    "url": "https://smk.lt/en/study-programmes/",
                    "link_label": "Atidaryti English study programmes",
                    "language": "EN"
                }
            )
        )

    return docs


def build_contact_documents(data: dict) -> list[Document]:
    docs = []
    contacts = data.get("contacts", {})

    docs.append(
        Document(
            id="contacts_general",
            text=(
                f"Bendra SMK kontaktinė informacija. "
                f"Bendras el. paštas: {contacts.get('general_email', 'Nenurodyta')}. "
                f"Priėmimo el. paštas: {contacts.get('admission_email', 'Nenurodyta')}. "
                f"Kontaktų puslapis: {contacts.get('main_contact_page', 'https://smk.lt/kontaktai/')}. "
                f"{contacts.get('admission_contacts_note', '')}"
            ),
            metadata={
                "category": "contact",
                "name": "Bendri kontaktai",
                "url": contacts.get("main_contact_page", "https://smk.lt/kontaktai/"),
                "link_label": "Atidaryti kontaktų puslapį"
            }
        )
    )

    for city in contacts.get("cities", []):
        city_name = city.get("city", "Nenurodyta")
        docs.append(
            Document(
                id=f"contact_{slugify(city_name)}",
                text=(
                    f"Kur yra SMK {city_name} padalinys? "
                    f"SMK {city_name} padalinio adresas yra {city.get('address', 'Nenurodyta')}. "
                    f"Kontaktai: telefonai {', '.join(city.get('phones', [])) or 'Nenurodyta'}. "
                    f"El. paštai: {', '.join(city.get('emails', [])) or 'Nenurodyta'}."
                ),
                metadata={
                    "category": "contact",
                    "name": city_name,
                    "city": city_name,
                    "url": city.get("url", contacts.get("main_contact_page", "https://smk.lt/kontaktai/")),
                    "link_label": f"Atidaryti {city_name} puslapį"
                }
            )
        )

    return docs


def build_admission_documents(data: dict) -> list[Document]:
    docs = []
    admission = data.get("admission", {})

    docs.append(
        Document(
            id="admission_general",
            text=(
                f"Stojimo į SMK informacija. "
                f"{admission.get('summary', '')} "
                f"Registracijos įmoka yra {admission.get('registration_fee', 'Nenurodyta')}. "
                f"Atskirasis priėmimas vyksta nuo "
                f"{admission.get('separate_admission_period', {}).get('start', 'Nenurodyta')} iki "
                f"{admission.get('separate_admission_period', {}).get('end', 'Nenurodyta')}. "
                f"Prašymus galima teikti šiais būdais: {', '.join(admission.get('application_methods', []))}."
            ),
            metadata={
                "category": "admission",
                "name": "Stojimas",
                "url": admission.get("main_url", "https://smk.lt/stojimas/"),
                "link_label": "Atidaryti stojimo puslapį"
            }
        )
    )

    required_docs = data.get("required_documents", [])
    if required_docs:
        docs.append(
            Document(
                id="admission_required_documents",
                text=(
                    "Stojimui į SMK reikalingi dokumentai: "
                    + "; ".join(required_docs) + "."
                ),
                metadata={
                    "category": "admission",
                    "name": "Reikalingi dokumentai",
                    "url": admission.get("admission_info_url", "https://smk.lt/priemimas/"),
                    "link_label": "Atidaryti priėmimo informaciją"
                }
            )
        )

    motivation = data.get("motivation_evaluation", {})
    if motivation:
        docs.append(
            Document(
                id="admission_motivation",
                text=(
                    f"Motyvacijos vertinimas SMK. "
                    f"{motivation.get('summary', '')} "
                    f"Registracija: {motivation.get('registration', 'Nenurodyta')}. "
                    f"Periodas nuo {motivation.get('period', {}).get('start', 'Nenurodyta')} "
                    f"iki {motivation.get('period', {}).get('end', 'Nenurodyta')}."
                ),
                metadata={
                    "category": "admission",
                    "name": "Motyvacijos vertinimas",
                    "url": admission.get("admission_info_url", "https://smk.lt/priemimas/"),
                    "link_label": "Atidaryti priėmimo informaciją"
                }
            )
        )

    higher_course = data.get("higher_course_admission", {})
    if higher_course.get("available"):
        docs.append(
            Document(
                id="admission_higher_course",
                text=(
                    f"Priėmimas į aukštesnius kursus SMK. "
                    f"{higher_course.get('summary', '')}"
                ),
                metadata={
                    "category": "admission",
                    "name": "Aukštesni kursai",
                    "url": admission.get("admission_info_url", "https://smk.lt/priemimas/"),
                    "link_label": "Atidaryti priėmimo informaciją"
                }
            )
        )

    return docs


def build_short_cycle_documents(data: dict) -> list[Document]:
    docs = []

    for item in data.get("short_cycle_programs", []):
        name = item.get("name", "Nenurodyta")
        docs.append(
            Document(
                id=f"short_cycle_{slugify(name)}",
                text=(
                    f"Trumpųjų studijų programa {name}. "
                    f"Kvalifikacija: {item.get('qualification', 'Nenurodyta')}. "
                    f"Trukmė: {item.get('duration_nl', 'Nenurodyta')}. "
                    f"Miestai: {', '.join(item.get('city_options', [])) or 'Nenurodyta'}. "
                    f"Kaina: {item.get('semester_price', 'Nenurodyta')} už semestrą ir "
                    f"{item.get('year_price', 'Nenurodyta')} už metus."
                ),
                metadata={
                    "category": "short_cycle",
                    "name": name,
                    "url": "https://smk.lt/priemimas/",
                    "link_label": "Atidaryti priėmimo puslapį"
                }
            )
        )

    return docs


def build_professional_training_documents(data: dict) -> list[Document]:
    docs = []
    prof = data.get("professional_training", {})

    docs.append(
        Document(
            id="professional_training_general",
            text=(
                f"Profesinis mokymas SMK. "
                f"{prof.get('summary', '')} "
                f"Reikalavimas stojant: {prof.get('entry_requirement', 'Nenurodyta')}. "
                f"Formos: {', '.join(prof.get('forms', []))}. "
                f"Trukmė: {prof.get('duration_summary', 'Nenurodyta')}. "
                f"Suteikiama kvalifikacija: {prof.get('qualification_awarded', 'Nenurodyta')}."
            ),
            metadata={
                "category": "professional_training",
                "name": "Profesinis mokymas",
                "url": "https://smk.lt/priemimas/",
                "link_label": "Atidaryti priėmimo puslapį"
            }
        )
    )

    for item in prof.get("programs", []):
        name = item.get("name", "Nenurodyta")
        docs.append(
            Document(
                id=f"professional_{slugify(name)}",
                text=(
                    f"Profesinio mokymo programa {name}. "
                    f"Pirminio mokymo trukmė: {item.get('primary_duration', 'Nenurodyta')}. "
                    f"Pirminio mokymo kaina: {item.get('primary_price', 'Nenurodyta')}. "
                    f"Tęstinio mokymo trukmė: {item.get('continuing_duration', 'Nenurodyta')}. "
                    f"Tęstinio mokymo kaina: {item.get('continuing_price', 'Nenurodyta')}."
                ),
                metadata={
                    "category": "professional_training",
                    "name": name,
                    "url": "https://smk.lt/priemimas/",
                    "link_label": "Atidaryti priėmimo puslapį"
                }
            )
        )

    return docs


def build_student_resource_documents(data: dict) -> list[Document]:
    docs = []

    for item in data.get("student_resources", []):
        name = item.get("name", "Nenurodyta")
        docs.append(
            Document(
                id=f"student_resource_{slugify(name)}",
                text=(
                    f"SMK studentų resursas {name}. "
                    f"{item.get('description', '')}"
                ),
                metadata={
                    "category": "student_resource",
                    "name": name,
                    "url": item.get("url", "https://smk.lt/studentams/"),
                    "link_label": f"Atidaryti {name}"
                }
            )
        )

    return docs


def build_faq_documents(data: dict) -> list[Document]:
    docs = []

    for idx, item in enumerate(data.get("faq", []), start=1):
        question = item.get("question", "Nenurodyta")
        answer = item.get("answer", "")
        docs.append(
            Document(
                id=f"faq_{idx}",
                text=(
                    f"Klausimas: {question} Atsakymas: {answer}"
                ),
                metadata={
                    "category": "faq",
                    "name": question,
                    "url": item.get("url", "https://smk.lt/"),
                    "link_label": "Atidaryti susijusį puslapį"
                }
            )
        )

    return docs

def build_pdf_documents() -> list[Document]:
    docs = []

    project_root = Path(__file__).resolve().parent.parent
    pdf_dir = project_root / "data" / "pdfs"

    pdf_items = load_pdf_documents(pdf_dir)

    for pdf_item in pdf_items:
        chunks = chunk_text(pdf_item["text"], chunk_size=1200, overlap=200)

        for idx, chunk in enumerate(chunks, start=1):
            docs.append(
                Document(
                    id=f"pdf_{slugify(pdf_item['title'])}_{idx}",
                    text=chunk,
                    metadata={
                        "category": "pdf",
                        "name": pdf_item["title"],
                        "filename": pdf_item["filename"],
                        "url": "",
                        "link_label": f"PDF: {pdf_item['title']}",
                        "chunk_index": idx,
                    }
                )
            )

    return docs