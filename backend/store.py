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
