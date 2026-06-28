"""Document ingestion orchestration."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Document, DocumentType
from app.services.chunking import chunk_text
from app.services.chroma_store import get_chroma_store
from app.services.text_extraction import extract_text_from_bytes, extract_text_from_file

DOC_TYPE_BY_FOLDER = {
    "specs": DocumentType.SPECIFICATION.value,
    "submittals": DocumentType.SUBMITTAL.value,
    "rfis": DocumentType.RFI.value,
    "change_orders": DocumentType.CHANGE_ORDER.value,
    "meeting_minutes": DocumentType.MEETING_MINUTES.value,
    "procurement": DocumentType.OTHER.value,
    "commissioning": DocumentType.COMMISSIONING.value,
}


def infer_doc_type(relative_path: Path) -> str:
    top_folder = relative_path.parts[0] if relative_path.parts else ""
    return DOC_TYPE_BY_FOLDER.get(top_folder, DocumentType.OTHER.value)


def ingest_document(
    db: Session,
    *,
    project_id: int,
    filename: str,
    content: bytes,
    doc_type: str | None = None,
    source_path: str | None = None,
) -> Document:
    existing = (
        db.query(Document)
        .filter(Document.project_id == project_id, Document.filename == filename)
        .first()
    )
    if existing:
        return existing

    text = extract_text_from_bytes(content, filename)
    document = Document(
        project_id=project_id,
        doc_type=doc_type or DocumentType.OTHER.value,
        filename=filename,
        parsed_text=text,
        metadata_json={"source_path": source_path or filename, "char_count": len(text)},
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    _index_document(document)
    return document


def ingest_file_path(db: Session, *, project_id: int, file_path: Path, data_root: Path) -> Document:
    relative = file_path.relative_to(data_root)
    doc_type = infer_doc_type(relative)
    return ingest_document(
        db,
        project_id=project_id,
        filename=str(relative).replace("\\", "/"),
        content=file_path.read_bytes(),
        doc_type=doc_type,
        source_path=str(relative).replace("\\", "/"),
    )


def ingest_data_directory(db: Session, project_id: int) -> dict:
    data_root = settings.data_dir_resolved
    stats = {"ingested": 0, "skipped": 0, "errors": []}

    if not data_root.exists():
        stats["errors"].append(f"Data directory not found: {data_root}")
        return stats

    for file_path in sorted(data_root.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in {".md", ".txt", ".pdf", ".markdown"}:
            continue
        if file_path.name == ".gitkeep":
            continue

        relative_name = str(file_path.relative_to(data_root)).replace("\\", "/")
        exists = (
            db.query(Document)
            .filter(Document.project_id == project_id, Document.filename == relative_name)
            .first()
        )
        if exists:
            stats["skipped"] += 1
            continue

        try:
            ingest_file_path(db, project_id=project_id, file_path=file_path, data_root=data_root)
            stats["ingested"] += 1
        except Exception as exc:  # noqa: BLE001
            stats["errors"].append(f"{relative_name}: {exc}")

    return stats


def _index_document(document: Document) -> None:
    chunks = chunk_text(document.parsed_text or "", settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        return

    store = get_chroma_store()
    store.delete_document_chunks(document.id)

    ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict] = []

    for index, chunk in enumerate(chunks):
        chunk_id = f"doc-{document.id}-chunk-{index}"
        ids.append(chunk_id)
        texts.append(chunk)
        metadatas.append(
            {
                "document_id": document.id,
                "project_id": document.project_id,
                "doc_type": document.doc_type,
                "source_file": document.filename,
                "chunk_index": index,
            }
        )

    store.upsert_chunks(ids=ids, texts=texts, metadatas=metadatas)


def reindex_all_documents(db: Session, project_id: int) -> int:
    documents = db.query(Document).filter(Document.project_id == project_id).all()
    for document in documents:
        _index_document(document)
    return len(documents)
