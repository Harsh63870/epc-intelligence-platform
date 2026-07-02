"""RFI Copilot API routes."""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.rfi_agent import answer_rfi_query, find_similar_rfis
from app.database import get_db
from app.models import RFI

router = APIRouter(prefix="/rfi", tags=["rfi"])


class RFIChatRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=2000)
    project_id: int = 1


class CitationOut(BaseModel):
    source_file: str
    doc_type: str | None = None
    excerpt: str


class SimilarRFIOut(BaseModel):
    id: int
    number: str
    subject: str
    response: str | None
    similarity: float


class RFIChatResponse(BaseModel):
    answer: str
    citations: list[CitationOut]
    similar_rfis: list[SimilarRFIOut]
    confidence: str
    estimated_manual_minutes: int
    groq_used: bool


class RFIOut(BaseModel):
    id: int
    number: str
    subject: str
    question: str
    response: str | None
    status: str

    model_config = {"from_attributes": True}


@router.post("/chat", response_model=RFIChatResponse)
def rfi_chat(body: RFIChatRequest, db: Session = Depends(get_db)) -> RFIChatResponse:
    result = answer_rfi_query(db, body.query, body.project_id)
    return RFIChatResponse(**result)


@router.get("/similar", response_model=list[SimilarRFIOut])
def rfi_similar(
    q: str = Query(..., min_length=2),
    project_id: int = Query(default=1),
    db: Session = Depends(get_db),
) -> list[SimilarRFIOut]:
    return [SimilarRFIOut(**item) for item in find_similar_rfis(db, q, project_id)]


@router.get("/list", response_model=list[RFIOut])
def list_rfis(project_id: int = Query(default=1), db: Session = Depends(get_db)) -> list[RFI]:
    return db.query(RFI).filter(RFI.project_id == project_id).order_by(RFI.number).all()
