"""ChromaDB vector store."""
from __future__ import annotations

from functools import lru_cache

import chromadb

from app.config import settings
from app.services.embeddings import embed_texts

COLLECTION_NAME = "project_documents"


class ChromaStore:
    def __init__(self) -> None:
        settings.chroma_path_resolved.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(settings.chroma_path_resolved))
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(
        self,
        *,
        ids: list[str],
        texts: list[str],
        metadatas: list[dict],
    ) -> None:
        embeddings = embed_texts(texts)
        self._collection.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

    def search(self, query: str, project_id: int, top_k: int = 8) -> list[dict]:
        query_embedding = embed_texts([query])[0]
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"project_id": project_id},
        )

        items: list[dict] = []
        if not results["ids"] or not results["ids"][0]:
            return items

        for idx, chunk_id in enumerate(results["ids"][0]):
            items.append(
                {
                    "id": chunk_id,
                    "text": results["documents"][0][idx] if results["documents"] else "",
                    "metadata": results["metadatas"][0][idx] if results["metadatas"] else {},
                    "distance": results["distances"][0][idx] if results.get("distances") else None,
                }
            )
        return items

    def delete_document_chunks(self, document_id: int) -> None:
        existing = self._collection.get(where={"document_id": document_id})
        if existing["ids"]:
            self._collection.delete(ids=existing["ids"])

    def count(self) -> int:
        return self._collection.count()


@lru_cache(maxsize=1)
def get_chroma_store() -> ChromaStore:
    return ChromaStore()
