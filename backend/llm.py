from __future__ import annotations
 
import os
from typing import List
 
import requests
import sys
 
_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
 

_GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash").strip()
_GEMINI_BASE = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
 
SYSTEM_PROMPT = (
    "You are a precise assistant. Answer the user's question using ONLY the "
    "provided context passages. Cite sources inline like [1], [2] matching the "
    "passage numbers. If the answer is not in the context, say you don't know."
)
 
 
def is_available() -> bool:
    """LLM is available if either an OpenAI-compatible key or a Gemini key is set."""
    return bool(_API_KEY or _GEMINI_KEY)
 
 
def generate(question: str, contexts: List[dict], timeout: int = 30) -> str:
    """Call the LLM to synthesize an answer from retrieved contexts."""
    if not is_available():
        raise RuntimeError("LLM is not configured. Set OPENAI_API_KEY or GEMINI_API_KEY to enable it.")
 
    context_block = "\n\n".join(
        f"[{i + 1}] (source: {c['doc']}"
        + (f", p.{c['page']}" if c.get("page") else "")
        + f")\n{c['text']}"
        for i, c in enumerate(contexts)
    )
    user_msg = f"Context passages:\n{context_block}\n\nQuestion: {question}\n\nAnswer:"

    # Debug: how many contexts and average length (do not print contents)
    try:
        ctx_count = len(contexts)
        avg_len = sum(len(c.get("text", "")) for c in contexts) // max(1, ctx_count)
    except Exception:
        ctx_count = 0
        avg_len = 0
    # Also list which documents/pages are included (doc names only).
    try:
        docs = ", ".join(f"{c.get('doc')}" + (f":p{c.get('page')}" if c.get('page') else "") for c in contexts)
    except Exception:
        docs = ""
    print(f"[llm] contexts={ctx_count} avg_len={avg_len} docs=[{docs}]", file=sys.stderr)
 
    
    use_provider = None
    if _GEMINI_KEY:
        use_provider = "gemini"
    elif _API_KEY:
        use_provider = "openai"
 
    print(f"[llm] provider_flags: OPENAI={bool(_API_KEY)} GEMINI={bool(_GEMINI_KEY)} chosen={use_provider}", file=sys.stderr)
 
    if use_provider == "openai":
        # Debug: show prompt length (approx)
        try:
            prompt_len = len(SYSTEM_PROMPT) + len(user_msg)
        except Exception:
            prompt_len = 0
        print(f"[llm] openai_prompt_len={prompt_len}", file=sys.stderr)
        try:
            resp = requests.post(
                f"{_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {_API_KEY}",
                         "Content-Type": "application/json"},
                json={
                    "model": _MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg},
                    ],
                    "temperature": 0.1,
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except requests.HTTPError as exc:
            # Log OpenAI error (do not print keys)
            try:
                status = exc.response.status_code  # type: ignore[attr-defined]
                body = exc.response.text[:1000] if exc.response is not None else ""
            except Exception:
                status = None
                body = ""
            print(f"[llm] OpenAI request failed: status={status} body={body}", file=sys.stderr)
            raise
