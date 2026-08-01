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
 
