"""Document ingestion: extract text from PDF/DOCX/TXT and split into chunks.

Chunks are the atomic units that get embedded and retrieved. We use a
sentence-aware sliding window with overlap so that context isn't cut mid-idea
and adjacent chunks share a little context for better recall.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class Chunk:
    id: int
    doc: str
    text: str
    # Approximate page number (PDF only), else None.
    page: int | None = None


@dataclass
class Document:
    name: str
    text: str
    chunks: List[Chunk] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Text extraction
# --------------------------------------------------------------------------- #
def extract_text(filename: str, data: bytes) -> tuple[str, List[tuple[int, str]]]:
    """Return (full_text, [(page_number, page_text), ...]).

    For non-PDF formats there's a single "page".
    """
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return _extract_pdf(data)
    if lower.endswith(".docx"):
        text = _extract_docx(data)
        return text, [(1, text)]
    if lower.endswith((".txt", ".md")):
        text = data.decode("utf-8", errors="ignore")
        return text, [(1, text)]
    raise ValueError(f"Unsupported file type: {filename}. Use PDF, DOCX, TXT or MD.")


def _extract_pdf(data: bytes) -> tuple[str, List[tuple[int, str]]]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages: List[tuple[int, str]] = []
    parts: List[str] = []
    for i, page in enumerate(reader.pages, start=1):
        txt = page.extract_text() or ""
        pages.append((i, txt))
        parts.append(txt)
    return "\n".join(parts), pages


def _extract_docx(data: bytes) -> str:
    from docx import Document as Docx

    doc = Docx(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)
