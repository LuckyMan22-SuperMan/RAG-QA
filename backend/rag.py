"""RAG orchestration: retrieve relevant chunks, then produce an answer.

Two answer modes:
  * "extractive" (default, offline): stitch together the best-matching
    sentences from the top chunks and highlight query terms. No LLM needed.
  * "generative" (optional): pass the retrieved context to an LLM to write a
    fluent, cited answer. Requires OPENAI_API_KEY.
"""

from __future__ import annotations

import re
from typing import Dict, List

from backend import llm
from backend.store import store

_WORD = re.compile(r"[A-Za-z0-9']+")
_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are",
    "was", "were", "be", "with", "as", "by", "at", "it", "this", "that", "what",
    "which", "who", "how", "why", "when", "where", "do", "does", "did", "can",
    "i", "you", "we", "they", "he", "she", "from", "about", "into",
} #these wrds are removed from the query to improve search results


def _keywords(question: str) -> List[str]:
    return [w.lower() for w in _WORD.findall(question) if w.lower() not in _STOP and len(w) > 1]


def _split_sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _extractive_answer(question: str, contexts: List[Dict], max_sentences: int = 3) -> str:
    """Pick the sentences across top contexts that best cover the query terms."""
    kws = set(_keywords(question))
    scored: List[tuple[float, int, str]] = []
    for ci, c in enumerate(contexts):
        for sent in _split_sentences(c["text"]):
            words = set(w.lower() for w in _WORD.findall(sent))
            overlap = len(kws & words)
            if overlap == 0:
                continue
            # Reward query coverage, lightly favour higher-ranked chunks.
            score = overlap + c["score"] - 0.01 * ci
            scored.append((score, ci, sent))
    if not scored:
        # Fall back to the single most relevant chunk's opening.
        return contexts[0]["text"][:400] + "..." if contexts else ""
    scored.sort(key=lambda t: t[0], reverse=True)
    chosen = []
    seen = set()
    for score, ci, sent in scored:
        if sent in seen:
            continue
        seen.add(sent)
        chosen.append((ci, sent))
        if len(chosen) >= max_sentences:
            break
    # Present in chunk order for readability, with citation markers.
    chosen.sort(key=lambda t: t[0])
    return " ".join(f"{sent} [{ci + 1}]" for ci, sent in chosen)


def answer(question: str, top_k: int = 5, mode: str = "auto") -> Dict:
    """Retrieve context and answer the question."""
    question = (question or "").strip()
    if not question:
        raise ValueError("Please enter a question.")

    contexts = store.search(question, top_k=top_k)
    
    print(f"[rag] question='{question}' keywords={_keywords(question)} top_k={top_k} contexts_count={len(contexts)}")
    if not contexts:
        return {
            "answer": "No documents indexed yet, or nothing relevant was found. "
                      "Upload documents and try again.",
            "mode": "none", "sources": [], "keywords": _keywords(question),
        }

    use_llm = mode == "generative" or (mode == "auto" and llm.is_available())
    used_mode = "extractive"
    llm_error = None
    if use_llm:
        try:
            ans = llm.generate(question, contexts)
            used_mode = "generative"
        except Exception as exc:  # noqa: BLE001 - fall back gracefully
            llm_error = str(exc)
            ans = _extractive_answer(question, contexts)
    else:
        ans = _extractive_answer(question, contexts)

    return {
        "answer": ans,
        "mode": used_mode,
        "llm_error": llm_error,
        "keywords": _keywords(question),
        "sources": [
            {
                "n": i + 1, "doc": c["doc"], "page": c["page"],
                "score": c["score"], "text": c["text"],
            }
            for i, c in enumerate(contexts)
        ],
    }
