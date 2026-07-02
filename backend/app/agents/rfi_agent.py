"""RFI Knowledge Agent — RAG over project documents with similar-RFI detection."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AuditEvent, RFI, RFIStatus
from app.services.chroma_store import get_chroma_store
from app.services.embeddings import embed_texts
from app.services.groq_client import GroqError, chat_completion, parse_json_response

MANUAL_EFFORT_MINUTES = 60


def _format_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata") or {}
        source = meta.get("source_file", "unknown")
        parts.append(f"[Source {i}: {source}]\n{chunk.get('text', '')}")
    return "\n\n---\n\n".join(parts)


def _build_citations(chunks: list[dict]) -> list[dict]:
    citations = []
    seen: set[str] = set()
    for chunk in chunks:
        meta = chunk.get("metadata") or {}
        source = meta.get("source_file", "unknown")
        if source in seen:
            continue
        seen.add(source)
        citations.append(
            {
                "source_file": source,
                "doc_type": meta.get("doc_type"),
                "excerpt": (chunk.get("text") or "")[:300],
            }
        )
    return citations


def find_similar_rfis(db: Session, query: str, project_id: int, limit: int = 3) -> list[dict]:
    rfis = (
        db.query(RFI)
        .filter(RFI.project_id == project_id, RFI.status == RFIStatus.ANSWERED.value)
        .all()
    )
    if not rfis:
        return []

    texts = [f"{r.subject}. {r.question}" for r in rfis]
    query_vec = embed_texts([query])[0]
    rfi_vecs = embed_texts(texts)

    scored: list[tuple[float, RFI]] = []
    for rfi, vec in zip(rfis, rfi_vecs):
        score = _cosine_similarity(query_vec, vec)
        scored.append((score, rfi))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, rfi in scored[:limit]:
        if score < 0.35:
            continue
        results.append(
            {
                "id": rfi.id,
                "number": rfi.number,
                "subject": rfi.subject,
                "response": rfi.response,
                "similarity": round(score, 3),
            }
        )
    return results


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _fallback_answer(query: str, chunks: list[dict], similar_rfis: list[dict]) -> dict:
    if not chunks:
        return {
            "answer": "I could not find relevant information in the project document corpus. "
            "Please ensure demo data has been seeded.",
            "citations": [],
            "similar_rfis": similar_rfis,
            "confidence": "low",
            "estimated_manual_minutes": MANUAL_EFFORT_MINUTES,
            "groq_used": False,
        }

    top = chunks[0]
    meta = top.get("metadata") or {}
    source = meta.get("source_file", "project records")
    excerpt = (top.get("text") or "")[:500]
    answer = (
        f"Based on project records in `{source}`:\n\n{excerpt}\n\n"
        "(Configure GROQ_API_KEY in backend/.env for full AI-generated answers with citations.)"
    )
    return {
        "answer": answer,
        "citations": _build_citations(chunks),
        "similar_rfis": similar_rfis,
        "confidence": "medium",
        "estimated_manual_minutes": MANUAL_EFFORT_MINUTES,
        "groq_used": False,
    }


def answer_rfi_query(db: Session, query: str, project_id: int = 1) -> dict:
    store = get_chroma_store()
    chunks = store.search(query, project_id=project_id, top_k=8)
    similar_rfis = find_similar_rfis(db, query, project_id)

    if not chunks:
        return _fallback_answer(query, chunks, similar_rfis)

    context = _format_context(chunks)
    similar_context = ""
    if similar_rfis:
        similar_context = "\n\nPreviously resolved similar RFIs:\n" + "\n".join(
            f"- {r['number']}: {r['subject']} → {r['response']}" for r in similar_rfis
        )

    system = (
        "You are an EPC project intelligence assistant for data centre construction. "
        "Answer ONLY using the provided project context. "
        "If the answer is not in the context, say you cannot find it in project records. "
        "Be concise and technical. Reference source filenames when citing facts. "
        "Return valid JSON with keys: answer (string), confidence (high|medium|low)."
    )
    user = f"Context:\n{context}{similar_context}\n\nQuestion: {query}"

    try:
        raw = chat_completion(system=system, user=user, json_mode=True)
        parsed = parse_json_response(raw)
        answer = parsed.get("answer", raw)
        confidence = parsed.get("confidence", "medium")
        groq_used = True
    except GroqError:
        return _fallback_answer(query, chunks, similar_rfis)

    citations = _build_citations(chunks)

    db.add(
        AuditEvent(
            project_id=project_id,
            entity_type="rfi_query",
            action=f"RFI copilot answered: {query[:120]}",
            actor="rfi_agent",
            metadata_json={"confidence": confidence, "citation_count": len(citations)},
        )
    )
    db.commit()

    return {
        "answer": answer,
        "citations": citations,
        "similar_rfis": similar_rfis,
        "confidence": confidence,
        "estimated_manual_minutes": MANUAL_EFFORT_MINUTES,
        "groq_used": groq_used,
    }
