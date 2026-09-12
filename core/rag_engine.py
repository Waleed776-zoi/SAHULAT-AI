"""
Lightweight retrieval layer for the follow-up chat feature.

PERFORMANCE (PERF-01/02/03): the curated catalogue is a handful of short
documents, so semantic retrieval buys very little while costing ~25-30s of
startup (PyTorch + sentence-transformers import, then a 199-shard model load)
and a live Hugging Face network round-trip.

So semantic search is now OPT-IN. By default this module uses keyword search,
which is instant, needs no model, and works with no network at all. Set

    SAHULAT_SEMANTIC_SEARCH=1

to enable the multilingual embedding path (worth it once the catalogue grows,
or when testing Urdu-question -> English-record retrieval).

Either way, building the index is LAZY - nothing here is imported or loaded
until someone actually asks a follow-up question.
"""
from __future__ import annotations

import logging
import os
from typing import List, Optional

from core.models import Opportunity

log = logging.getLogger(__name__)

_COLLECTION_NAME = "sahulat_opportunities"
_EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

MODE_SEMANTIC = "semantic"
MODE_KEYWORD = "keyword"


def semantic_enabled() -> bool:
    """Semantic search is opt-in; see the module docstring."""
    return os.environ.get("SAHULAT_SEMANTIC_SEARCH", "0").strip().lower() in ("1", "true", "yes")


def _force_offline_model_loading() -> None:
    """
    PERF-02: the embedding model is cached on disk, but the loader still calls
    the Hugging Face Hub to check revisions - ~6s of round-trip on startup, and
    a hang (not a fast failure) on slow or captive-portal wifi. Pin it offline
    so a cached model really is usable without a network.
    """
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


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
    if o.name_ur:
        parts.append(f"Name (Urdu): {o.name_ur}")
    if o.summary_ur:
        parts.append(f"Summary (Urdu): {o.summary_ur}")
    return "\n".join(parts)


# Words too common to carry meaning in a 3-document corpus.
_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "am", "do", "does",
    "did", "for", "of", "to", "in", "on", "at", "by", "with", "from", "and", "or",
    "but", "if", "then", "than", "that", "this", "these", "those", "it", "its",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "they", "them",
    "what", "which", "who", "whom", "how", "when", "where", "why", "can", "could",
    "should", "would", "will", "shall", "may", "might", "must", "have", "has", "had",
    "get", "got", "need", "want", "about", "any", "some", "all",
}


class RagIndex:
    """
    Retrieval over the curated catalogue.

    `mode` reports which path is actually live so the UI and a developer can
    both see it - the old code swallowed every failure into an identical silent
    fallback with no way to tell (OPS-03).
    """

    def __init__(self, opportunities: List[Opportunity], allow_semantic: Optional[bool] = None):
        self.opportunities = opportunities
        self._docs = [_opportunity_to_text(o) for o in opportunities]
        self._chroma_collection = None
        self.mode = MODE_KEYWORD
        self.fallback_reason: Optional[str] = None

        if allow_semantic is None:
            allow_semantic = semantic_enabled()
        if allow_semantic:
            self._try_build_chroma()
        else:
            self.fallback_reason = "semantic search not enabled (SAHULAT_SEMANTIC_SEARCH)"

    def _try_build_chroma(self) -> None:
        try:
            _force_offline_model_loading()
            import chromadb
            from chromadb.utils import embedding_functions

            client = chromadb.Client()
            embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=_EMBEDDING_MODEL
            )
            collection = client.get_or_create_collection(
                name=_COLLECTION_NAME, embedding_function=embed_fn
            )
            # upsert, not add: re-adding the same ids across sessions is a
            # no-op we don't want to depend on.
            collection.upsert(
                documents=self._docs,
                ids=[o.opportunity_id for o in self.opportunities],
            )
            self._chroma_collection = collection
            self.mode = MODE_SEMANTIC
        except Exception as exc:
            # chromadb/sentence-transformers missing, or the embedding model
            # isn't in the local cache. Keyword search still works, but record
            # WHY we fell back instead of failing silently (OPS-03).
            self.fallback_reason = f"{type(exc).__name__}: {exc}"
            log.warning("Semantic index unavailable, using keyword search (%s)",
                        self.fallback_reason)
            self._chroma_collection = None
            self.mode = MODE_KEYWORD

    def retrieve_for(self, opportunity_id: str, query: str) -> List[str]:
        """
        Evidence from ONE record (P1-3).

        When the user is asking about a specific opportunity, retrieving across
        the whole catalogue is worse than useless: it hands the model text
        about a different scheme labelled "evidence", which is exactly how a
        confident answer about the wrong scholarship gets produced.

        Returns the record's own text, or [] if that id is not in the index -
        never a near-miss from somewhere else.
        """
        if not query or not query.strip():
            return []
        for opportunity, document in zip(self.opportunities, self._docs):
            if opportunity.opportunity_id == opportunity_id:
                return [document]
        return []

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        if not query or not query.strip():
            return []

        if self._chroma_collection is not None:
            try:
                results = self._chroma_collection.query(query_texts=[query], n_results=top_k)
                return results.get("documents", [[]])[0]
            except Exception as exc:
                log.warning("Semantic query failed, using keyword search: %s", exc)

        return self._keyword_fallback(query, top_k)

    def _keyword_fallback(self, query: str, top_k: int) -> List[str]:
        """
        Score documents by meaningful term overlap.

        Returns [] when nothing matches. It used to return the first few
        documents regardless, which handed the model unrelated text labelled
        "Evidence" - exactly the grounding failure this architecture exists to
        prevent (BUG-06). No evidence is an honest answer.
        """
        query_terms = {w.strip(".,?!:;\"'()") for w in query.lower().split()}
        query_terms = {w for w in query_terms if w and w not in _STOPWORDS and len(w) > 2}
        if not query_terms:
            return []

        scored = []
        for doc in self._docs:
            doc_terms = {w.strip(".,?!:;\"'()") for w in doc.lower().split()}
            score = len(query_terms & doc_terms)
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]
