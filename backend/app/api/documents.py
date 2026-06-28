"""Document ingestion and vector search API."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Document, DocumentType
from app.services.chroma_store import get_chroma_store
from app.services.ingestion import ingest_document
from app.services.seed_service import get_or_create_project

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentOut(BaseModel):
    id: int
    project_id: int
    doc_type: str
    filename: str
    char_count: int | None = None

    model_config = {"from_attributes": True}


class SearchResult(BaseModel):
    id: str
    text: str
    metadata: dict
    distance: float | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total_vectors: int


@router.get("", response_model=list[DocumentOut])
def list_documents(
    project_id: int = Query(default=1),
    db: Session = Depends(get_db),
) -> list[DocumentOut]:
    docs = db.query(Document).filter(Document.project_id == project_id).order_by(Document.id).all()
    return [
        DocumentOut(
            id=d.id,
            project_id=d.project_id,
            doc_type=d.doc_type,
            filename=d.filename,
            char_count=(d.metadata_json or {}).get("char_count"),
        )
        for d in docs
    ]


@router.post("/ingest", response_model=DocumentOut)
async def ingest_upload(
    file: UploadFile = File(...),
    project_id: int = Form(default=1),
    doc_type: str = Form(default=DocumentType.OTHER.value),
    db: Session = Depends(get_db),
) -> DocumentOut:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    suffix = file.filename.lower().split(".")[-1]
    if suffix not in {"pdf", "md", "txt", "markdown"}:
        raise HTTPException(status_code=400, detail="Supported formats: pdf, md, txt")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    get_or_create_project(db)

    document = ingest_document(
        db,
        project_id=project_id,
        filename=f"uploads/{file.filename}",
        content=content,
        doc_type=doc_type,
    )
    return DocumentOut(
        id=document.id,
        project_id=document.project_id,
        doc_type=document.doc_type,
        filename=document.filename,
        char_count=(document.metadata_json or {}).get("char_count"),
    )


@router.get("/search", response_model=SearchResponse)
def search_documents(
    q: str = Query(..., min_length=2),
    project_id: int = Query(default=1),
    top_k: int = Query(default=8, ge=1, le=20),
) -> SearchResponse:
    store = get_chroma_store()
    results = store.search(q, project_id=project_id, top_k=top_k)
    return SearchResponse(
        query=q,
        results=[SearchResult(**item) for item in results],
        total_vectors=store.count(),
    )
