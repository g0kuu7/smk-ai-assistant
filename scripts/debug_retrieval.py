from rag.retriever import Retriever


def main():
    retriever = Retriever()

    while True:
        query = input("Query: ").strip()
        if not query:
            break

        results = retriever.retrieve(query, top_k=5)

        print("\nRESULTS:")
        for idx, result in enumerate(results, start=1):
            print(f"\n[{idx}] score={result.score}")
            print(f"id={result.id}")
            print(f"category={result.metadata.get('category')}")
            print(f"name={result.metadata.get('name')}")
            print(f"text={result.text}")
            print(f"url={result.metadata.get('url')}")
        print("-" * 80)


if __name__ == "__main__":
    main()