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
