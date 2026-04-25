import time
from pathlib import Path

import chromadb
from google import genai
from google.genai.errors import ClientError

from rag.config import (
    GEMINI_API_KEY,
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    GEMINI_EMBEDDING_MODEL,
)
from rag.schemas import Document, RetrievalResult


class VectorStore:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY nerastas .env faile")

        self.client = genai.Client(api_key=GEMINI_API_KEY)

        persist_path = Path(CHROMA_PERSIST_DIR).resolve()
        persist_path.mkdir(parents=True, exist_ok=True)

        self.chroma_client = chromadb.PersistentClient(path=str(persist_path))
        self.collection = self.chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME
        )

    def _embed_query(self, query: str) -> list[float]:
        response = self.client.models.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            contents=query,
            config={
                "task_type": "RETRIEVAL_QUERY"
            }
        )
        return response.embeddings[0].values

    def _embed_documents(self, texts: list[str], batch_size: int = 20) -> list[list[float]]:
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            while True:
                try:
                    response = self.client.models.embed_content(
                        model=GEMINI_EMBEDDING_MODEL,
                        contents=batch,
                        config={
                            "task_type": "RETRIEVAL_DOCUMENT"
                        }
                    )
                    batch_embeddings = [item.values for item in response.embeddings]
                    all_embeddings.extend(batch_embeddings)
                    break

                except ClientError as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        print("Pasiektas Gemini limitas, laukiu 60 s...")
                        time.sleep(60)
                    else:
                        raise

        return all_embeddings

    def reset(self) -> None:
        try:
            self.chroma_client.delete_collection(CHROMA_COLLECTION_NAME)
        except Exception:
            pass

        self.collection = self.chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME
        )

    def add_documents(self, documents: list[Document]) -> None:
        if not documents:
            return

        ids = [doc.id for doc in documents]
        texts = [doc.text for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        embeddings = self._embed_documents(texts)

        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        query_embedding = self._embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        output: list[RetrievalResult] = []

        for doc_id, doc_text, metadata, distance in zip(ids, docs, metadatas, distances):
            output.append(
                RetrievalResult(
                    id=doc_id,
                    text=doc_text,
                    metadata=metadata or {},
                    score=float(distance) if distance is not None else 0.0
                )
            )

        return output