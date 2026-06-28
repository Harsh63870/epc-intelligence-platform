"""Text chunking utilities."""
from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 320) -> list[str]:
    """Split text into overlapping chunks (~500 tokens at 4 chars/token)."""
    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not cleaned:
        return []

    chunks: list[str] = []
    start = 0
    length = len(cleaned)

    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            boundary = cleaned.rfind("\n\n", start, end)
            if boundary == -1:
                boundary = cleaned.rfind(". ", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary + 1

        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= length:
            break
        start = max(end - overlap, start + 1)

    return chunks
