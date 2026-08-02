"""In-memory TF-IDF vector store.

Holds all ingested chunks, fits a TF-IDF vectorizer over them, and answers
similarity queries via cosine similarity. Rebuilding on each ingest keeps the
implementation simple and is plenty fast for typical document sets.

Swapping this for dense embeddings (sentence-transformers) + FAISS is a
natural upgrade; the public interface (add/search/reset) would stay the same.
"""

from __future__ import annotations

import threading
from typing import Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.ingest import Chunk


class VectorStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._chunks: List[Chunk] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None  # sparse TF-IDF matrix aligned with self._chunks
        self._docs: Dict[str, int] = {}  # doc name -> chunk count

    # ------------------------------------------------------------------ #
    def add_chunks(self, chunks: List[Chunk]) -> None:
        with self._lock:
            self._chunks.extend(chunks)
            for c in chunks:
                self._docs[c.doc] = self._docs.get(c.doc, 0) + 1
            self._refit()
            # Debug: log that chunks were added and overall stats.
            try:
                print(f"[store] added {len(chunks)} chunks, total_chunks={len(self._chunks)}, docs={list(self._docs.keys())}")
            except Exception:
                pass

    def _refit(self) -> None:
        if not self._chunks:
            self._vectorizer, self._matrix = None, None
            return
        self._vectorizer = TfidfVectorizer(
            lowercase=True, stop_words="english",
            ngram_range=(1, 2), sublinear_tf=True, min_df=1,
        )
        self._matrix = self._vectorizer.fit_transform(c.text for c in self._chunks)

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        with self._lock:
            if not self._chunks or self._vectorizer is None:
                return []
            q_vec = self._vectorizer.transform([query])
            sims = cosine_similarity(q_vec, self._matrix)[0]
            top_k = min(top_k, len(sims))
            # Indices of the top_k highest similarities, sorted descending.
            top_idx = sims.argsort()[::-1][:top_k]
            results = []
            for idx in top_idx:
                score = float(sims[idx])
                c = self._chunks[idx]
                results.append({
                    "chunk_id": c.id, "doc": c.doc, "page": c.page,
                    "text": c.text, "score": round(score, 4),
                })
            return results

    # ------------------------------------------------------------------ #
    def remove_document(self, name: str) -> bool:
        """Drop all chunks belonging to a document and refit. Returns True if found."""
        with self._lock:
            if name not in self._docs:
                return False
            self._chunks = [c for c in self._chunks if c.doc != name]
            del self._docs[name]
            self._refit()
            return True

    def reset(self) -> None:
        with self._lock:
            self._chunks.clear()
            self._docs.clear()
            self._vectorizer, self._matrix = None, None

    def stats(self) -> Dict:
        with self._lock:
            return {
                "num_docs": len(self._docs),
                "num_chunks": len(self._chunks),
                "docs": [{"name": n, "chunks": c} for n, c in self._docs.items()],
                "vocab_size": len(self._vectorizer.vocabulary_) if self._vectorizer else 0,
            }


store = VectorStore()
