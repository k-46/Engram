import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv

load_dotenv()

from src.pipeline import EngramPipeline


def main() -> None:
    print("Engram Engineering Knowledge Assistant")
    pipeline = EngramPipeline()
    print(f"Indexed {pipeline.store.count()} chunks.")
    print("Type 'quit' to exit.\n")
    while True:
        question = input("Question: ").strip()
        if question.lower() in {"quit", "exit"}:
            break
        if not question:
            continue
        result = pipeline.answer(question)
        print("\nResponse:\n" + result["answer"])
        print("\nRetrieved sources:")
        for source in result["sources"]:
            print(
                f"- {source.document_id}: "
                f"{source.metadata.get('title', 'Untitled')} "
                f"(score={source.score:.3f})"
            )
        print()


if __name__ == "__main__":
    main()
