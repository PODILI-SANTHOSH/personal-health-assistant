from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {'.txt', '.pdf'}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def sanitize_filename(filename: str) -> str:
    candidate = Path(filename).name.replace('..', '')
    safe = ''.join(ch for ch in candidate if ch.isalnum() or ch in {'-', '_', '.', ' '})
    return safe.strip() or 'medical_document.txt'


def is_supported_file(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == '.txt':
        return path.read_text(encoding='utf-8', errors='ignore')
    if suffix == '.pdf':
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ''
            pages.append(text)
        return '\n'.join(pages)
    raise ValueError(f'Unsupported file type for {path.name}')
