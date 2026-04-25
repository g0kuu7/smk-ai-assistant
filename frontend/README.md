# SMK AI Assistant

SMK AI Assistant yra virtualus pokalbių asistentas, skirtas atsakyti į klausimus apie SMK studijas, programas, kainas, stojimą ir studentų sistemas.

Projektas naudoja dirbtinį intelektą (Gemini) ir RAG (Retrieval-Augmented Generation) metodą, kad pateiktų tikslius ir kontekstinius atsakymus.

---

## ✨ Funkcionalumas

- 💬 Chat tipo sąsaja (kaip ChatGPT)
- 🎓 Atsakymai apie SMK studijų programas, kainas, stojimą
- 📚 RAG sistema (atsakymai pagal duomenų bazę)
- 🤖 Bendri AI atsakymai (pvz. „Kas yra dirbtinis intelektas?“)
- 🔁 Pokalbio kontekstas (follow-up klausimai)
- ⚡ Greitas atsakymas su cache sistema
- 🛡️ Apsaugos:
  - rate limiting
  - netinkamų klausimų filtravimas
- 🔗 Nuorodos į oficialius SMK puslapius

---

## 🧠 Naudotos technologijos

### Backend
- Python
- Flask
- ChromaDB (vector database)
- Google Gemini API

### Frontend
- React
- CSS (custom UI)

---

## 🚀 Kaip paleisti projektą

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m backend.app

### 2. Frontend

cd frontend
npm install
npm run dev