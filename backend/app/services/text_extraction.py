"""Document text extraction."""
from __future__ import annotations

from pathlib import Path


def extract_text_from_bytes(content: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(content)
    if suffix in {".md", ".txt", ".markdown"}:
        return content.decode("utf-8", errors="replace")
    raise ValueError(f"Unsupported file type: {suffix}")


def extract_text_from_file(path: Path) -> str:
    return extract_text_from_bytes(path.read_bytes(), path.name)


def _extract_pdf(content: bytes) -> str:
    import fitz

    doc = fitz.open(stream=content, filetype="pdf")
    pages = [page.get_text("text") for page in doc]
    doc.close()
    return "\n\n".join(p.strip() for p in pages if p.strip())
