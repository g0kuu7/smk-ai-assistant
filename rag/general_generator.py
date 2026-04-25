from google import genai
from rag.config import GEMINI_API_KEY, GEMINI_CHAT_MODEL


GENERAL_SYSTEM_PROMPT = """
Tu esi profesionalus virtualus asistentas SMK svetainės demonstraciniame puslapyje.

Taisyklės:
- Atsakyk lietuvių kalba.
- Būk mandagus, aiškus, žmogiškas ir sklandus.
- Atsakyk taip, kaip atsakytų geras svetainės konsultantas, o ne techninis robotas.
- Naudok pokalbio istoriją, kad suprastum tęstinius atsakymus.
- Jei vartotojas sako „taip“, „turiu“, „taip turiu“ po tavo pasiūlymo padėti, paprašyk jo parašyti konkretų klausimą.
- Jei vartotojas klausia ne apie SMK, trumpai pasakyk, kad esi skirtas SMK informacijai.
- Jei klausimas apie SMK, nekurk tikslių faktų iš atminties. Geriau nukreipk žmogų klausti konkrečiau arba naudoti SMK informaciją.
- Jei atsakymas gali būti trumpas, atsakyk trumpai.
- Follow-up klausimą pridėk tik tada, kai jis tikrai naudingas.
- Nevartok techninių žodžių kaip „API“, „backend“, „modelis“, „klaida“.
"""


def answer_with_general_gemini(user_query: str, history: list[dict] | None = None) -> dict:
    history = history or []

    formatted_history = "\n".join(
        [f"{item.get('role', 'user')}: {item.get('text', '')}" for item in history[-8:]]
    )

    prompt = f"""
{GENERAL_SYSTEM_PROMPT}

Pokalbio istorija:
{formatted_history}

Vartotojo klausimas:
{user_query}

Atsakyk natūraliai, trumpai ir profesionaliai.
"""

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model=GEMINI_CHAT_MODEL,
            contents=prompt,
        )

        text = response.text.strip() if response.text else (
            "Atsiprašau, šiuo metu nepavyko paruošti atsakymo. Galite pabandyti patikslinti klausimą?"
        )

        return {
            "reply": text,
            "links": []
        }

    except Exception as e:
        print("[GENERAL GEMINI ERROR]", repr(e))

        return {
            "reply": (
                "Atsiprašau, šiuo metu nepavyko paruošti atsakymo. "
                "Pabandykite dar kartą po kelių minučių arba parašykite klausimą konkrečiau."
            ),
            "links": []
        }