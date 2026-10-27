from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.config import settings
from backend.services.document_loader import is_supported_file
from backend.services.rag_pipeline import rag_pipeline


def main() -> None:
    documents_dir = settings.DATA_DIR
    documents_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(documents_dir.glob('*'))
    if not files:
        print('No documents found in the medical_documents folder.')
        return
    for each in files:
        if each.is_file() and is_supported_file(each):
            print(f'Indexing {each.name}...')
            rag_pipeline.index_document(each)
    print('Document ingestion complete.')


if __name__ == '__main__':
    main()
