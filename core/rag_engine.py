"""
Lightweight retrieval layer for the follow-up chat feature.

For the hackathon MVP this indexes only the curated opportunity records
(a few dozen short documents at most), so a full production vector DB
server is overkill. ChromaDB running in-process (no separate server) is
enough - see requirements.txt.

If chromadb / sentence-transformers aren't installed yet (e.g. you're just
testing the rules engine), this module degrades to simple keyword search
over the same text so the rest of the app doesn't hard-crash.
"""
from __future__ import annotations

from typing import List
from core.models import Opportunity

_COLLECTION_NAME = "sahulat_opportunities"


def _opportunity_to_text(o: Opportunity) -> str:
    ec = o.eligibility_conditions
    parts = [
        f"Name: {o.name}",
        f"Category: {o.category}",
        f"Provider: {o.provider}",
        f"Summary: {o.summary_en}",
        f"Eligibility notes: {ec.special_quota_note or ''}",
        f"Required documents: {', '.join(o.required_documents)}",
        f"Application steps: {' -> '.join(o.application_steps)}",
        f"Official source: {o.official_url}",
    ]
    return "\n".join(parts)


class RagIndex:
    def __init__(self, opportunities: List[Opportunity]):
        self.opportunities = opportunities
        self._docs = [_opportunity_to_text(o) for o in opportunities]
        self._chroma_collection = None
        self._try_build_chroma()

    def _try_build_chroma(self) -> None:
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            client = chromadb.Client()
            embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="paraphrase-multilingual-MiniLM-L12-v2"
            )
            collection = client.get_or_create_collection(
                name=_COLLECTION_NAME, embedding_function=embed_fn
            )
            collection.add(
                documents=self._docs,
                ids=[o.opportunity_id for o in self.opportunities],
            )
            self._chroma_collection = collection
        except Exception:
            # chromadb/sentence-transformers not installed, or embedding
            # model couldn't be downloaded (no network in this environment).
            # Falls back to keyword search below - app stays functional.
            self._chroma_collection = None

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        if self._chroma_collection is not None:
            results = self._chroma_collection.query(query_texts=[query], n_results=top_k)
            return results.get("documents", [[]])[0]

        return self._keyword_fallback(query, top_k)

    def _keyword_fallback(self, query: str, top_k: int) -> List[str]:
        query_terms = set(query.lower().split())
        scored = []
        for doc in self._docs:
            doc_terms = set(doc.lower().split())
            score = len(query_terms & doc_terms)
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored[:top_k] if score > 0] or self._docs[:top_k]
