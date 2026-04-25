from google import genai

from rag.config import GEMINI_API_KEY, GEMINI_CHAT_MODEL


SYSTEM_PROMPT = """
Tu esi profesionalus SMK virtualus asistentas, įdiegtas SMK svetainėje.

Tavo tikslas:
- Atsakyti taip, kaip atsakytų labai gerai paruoštas, mandagus ir modernus svetainės konsultantas.
- Atsakymai turi būti aiškūs, žmogiški, trumpi ir naudingi.
- Naudok pokalbio istoriją, kad suprastum tęstinius atsakymus, pvz. „taip“, „turiu“, „o kiek?“, „o Vilniuje?“.
- Jei vartotojas tik patvirtina, kad turi klausimą, paprašyk jo parašyti konkretų klausimą.
- Jei klausimas apie SMK, remkis pateikta SMK informacija.
- Jei informacijos nepakanka, nekurk tikslių faktų. Mandagiai paprašyk patikslinti arba nukreipk į tinkamą SMK puslapį.
- Neatsakinėk techniškai. Nevartok žodžių „kontekstas“, „duomenų bazė“, „retrieval“, „modelis“, „API“, „backend“.
- Nerašyk sausai. Atsakymas turi skambėti kaip normalus pokalbis.
- Jei tinka, naudok 1–3 trumpus punktus.
- Follow-up klausimą pridėk tik tada, kai jis tikrai padeda vartotojui tęsti pokalbį.
- Nenaudok follow-up klausimo po kiekvieno atsakymo.
- Jei vartotojas dėkoja, atsakyk trumpai ir nebespausk tęsti pokalbio.
- Jei vartotojas prašo nuorodos, niekada nesakyk „nuorodos neturiu“, jeigu informacijoje yra URL arba sistema gali pateikti nuorodą žemiau.
- Jei programa yra „Programavimas ir multimedija“, jos nuoroda yra žinoma, todėl nesakyk, kad tiesioginės nuorodos neturi.
- „Ateities verslas ir dirbtinis intelektas“ nėra tiesioginė programavimo programa. Ją galima minėti tik kaip artimą technologijų / DI taikymo versle kryptį.
- Apie bendrabučius nekalbėk kaip apie faktą, jei pateiktoje informacijoje nėra aiškios informacijos.
- Atsakyk lietuvių kalba.
"""


class GeminiGenerator:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY nerastas .env faile")

        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate(
        self,
        user_query: str,
        context_chunks: list[str],
        history: list[dict] | None = None
    ) -> str:
        history = history or []

        formatted_history = "\n".join(
            [f"{item.get('role', 'user')}: {item.get('text', '')}" for item in history[-8:]]
        )

        formatted_context = "\n\n".join(
            [f"[SMK INFORMACIJA {idx + 1}]\n{chunk}" for idx, chunk in enumerate(context_chunks)]
        )

        prompt = f"""
{SYSTEM_PROMPT}

Pokalbio istorija:
{formatted_history}

SMK informacija:
{formatted_context}

Vartotojo klausimas:
{user_query}

Atsakymo instrukcija:
1. Atsakyk natūraliai, lyg kalbėtum su žmogumi SMK svetainės chat'e.
2. Jei klausimas aiškus ir SMK informacijoje yra atsakymas, pateik atsakymą trumpai ir tvarkingai.
3. Jei klausimas neaiškus arba vartotojas tik patvirtina, kad turi klausimą, paprašyk jo parašyti konkretų klausimą.
4. Jei tikslios informacijos nėra, pasakyk tai profesionaliai ir pasiūlyk patikslinti klausimą.
5. Follow-up klausimą pridėk tik tada, kai jis natūraliai reikalingas.
6. Nesakyk, kad neturi nuorodos, jei vartotojas prašo programos aprašymo — nuorodos gali būti pateikiamos kaip mygtukai po atsakymu.
"""

        response = self.client.models.generate_content(
            model=GEMINI_CHAT_MODEL,
            contents=prompt,
        )

        text = (response.text or "").strip()

        if not text:
            return "Atsiprašau, šiuo metu nepavyko paruošti atsakymo. Galite pabandyti patikslinti klausimą?"

        return text