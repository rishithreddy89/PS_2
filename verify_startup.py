#!/usr/bin/env python3
"""Verify backend can start successfully."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    print("\n" + "=" * 60)
    print("BACKEND STARTUP VERIFICATION")
    print("=" * 60 + "\n")

    # Check dependencies
    deps = [
        ("python-docx", "from docx import Document"),
        ("PyPDF2", "import PyPDF2"),
        ("sentence-transformers", "import sentence_transformers"),
        ("chromadb", "import chromadb"),
    ]

    print("Checking dependencies...")
    for name, import_stmt in deps:
        try:
            exec(import_stmt)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} NOT installed")
            return False

    print("\nChecking app imports...")
    try:
        from app.main import app
        print("  ✓ app.main imported")
    except Exception as e:
        print(f"  ✗ app.main import failed: {e}")
        return False

    print("\nChecking services...")
    try:
        from app.knowledge.local_embedding import get_local_embedding_service
        print("  ✓ LocalEmbeddingService available")
    except Exception as e:
        print(f"  ✗ LocalEmbeddingService failed: {e}")
        return False

    try:
        from app.knowledge.ingestion import get_ingestion_service
        print("  ✓ IngestionService available")
    except Exception as e:
        print(f"  ✗ IngestionService failed: {e}")
        return False

    try:
        from app.knowledge.chroma_service import get_chroma_service
        print("  ✓ ChromaDBService available")
    except Exception as e:
        print(f"  ✗ ChromaDBService failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("✓ All checks passed! Backend ready to start.")
    print("=" * 60 + "\n")
    print("Run: python3 -m uvicorn app.main:app --reload")
    print("     Or: ./run-backend.sh\n")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
