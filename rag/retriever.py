from backend.utils import normalize_text
from rag.vector_store import VectorStore


class Retriever:
    def __init__(self):
        self.store = VectorStore()

    def retrieve(self, query: str, top_k: int = 5):
        results = self.store.search(query=query, top_k=10)
        query_norm = normalize_text(query)

        boosted = []
        for result in results:
            score = result.score
            category = normalize_text(str(result.metadata.get("category", "")))
            name = normalize_text(str(result.metadata.get("name", "")))
            text = normalize_text(result.text)

            # mažesnis distance = geriau, todėl boost darysime mažindami score
            if "vilni" in query_norm and ("vilni" in name or "vilni" in text):
                score -= 0.12

            if ("kur" in query_norm or "adresas" in query_norm or "kontakt" in query_norm) and category == "contact":
                score -= 0.18

            if ("trump" in query_norm or "trumpuj" in query_norm) and category in {"short_cycle", "faq"}:
                score -= 0.14

            if ("kain" in query_norm or "kiek kainuoja" in query_norm) and category in {"price", "program"}:
                score -= 0.14

            if ("stoj" in query_norm or "dokument" in query_norm or "priem" in query_norm) and category == "admission":
                score -= 0.16

            if "moodle" in query_norm and "moodle" in name:
                score -= 0.25

            result.score = score
            boosted.append(result)

        boosted.sort(key=lambda x: x.score)
        return boosted[:top_k]