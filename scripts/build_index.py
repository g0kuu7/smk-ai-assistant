from backend.data_loader import load_smk_data
from rag.document_builder import build_documents
from rag.vector_store import VectorStore


def main():
    data = load_smk_data()
    documents = build_documents(data)

    store = VectorStore()
    store.reset()
    store.add_documents(documents)

    print(f"Indexed {len(documents)} documents into Chroma.")


if __name__ == "__main__":
    main()