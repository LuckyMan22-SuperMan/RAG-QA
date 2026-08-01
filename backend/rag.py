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
}
