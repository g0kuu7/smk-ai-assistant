from pathlib import Path
from pypdf import PdfReader


def extract_text_from_pdf(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages_text = []

    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages_text.append(text.strip())

    return "\n".join(pages_text)


def load_pdf_documents(pdf_dir: Path) -> list[dict]:
    documents = []

    if not pdf_dir.exists():
        return documents

    for pdf_file in pdf_dir.glob("*.pdf"):
        try:
            text = extract_text_from_pdf(pdf_file)

            if not text.strip():
                continue

            documents.append({
                "filename": pdf_file.name,
                "title": pdf_file.stem,
                "text": text,
            })
        except Exception as e:
            print(f"Nepavyko nuskaityti PDF {pdf_file.name}: {e}")

    return documents