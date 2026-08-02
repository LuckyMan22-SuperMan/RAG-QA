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


# --------------------------------------------------------------------------- #
# Chunking
# --------------------------------------------------------------------------- #
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _clean(text: str) -> str:
    text = text.replace("\r", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    """Sentence-aware sliding window producing ~chunk_size character chunks."""
    text = _clean(text)
    if not text:
        return []
    sentences = _SENT_SPLIT.split(text)
    chunks: List[str] = []
    current = ""
    for sent in sentences:
        if len(current) + len(sent) + 1 <= chunk_size:
            current = f"{current} {sent}".strip()
        else:
            if current:
                chunks.append(current)
            # Start new chunk, carrying overlap from the tail of the previous.
            if overlap and chunks:
                tail = chunks[-1][-overlap:]
                current = f"{tail} {sent}".strip()
            else:
                current = sent
            # A single very long sentence: hard-split it.
            while len(current) > chunk_size:
                chunks.append(current[:chunk_size])
                current = current[chunk_size - overlap:]
    if current:
        chunks.append(current)
    return chunks

