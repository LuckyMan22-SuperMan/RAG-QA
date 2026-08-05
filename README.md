# RAG Document Q&A ("Chat with your Documents")

A full-stack **Retrieval-Augmented Generation** app: upload PDFs/DOCX/TXT,
and ask questions to get answers **with cited sources**. Retrieval uses a
**scikit-learn TF-IDF** vector store. Answers are
**extractive by default** (no API key needed) and can optionally be
**LLM-generated** when an API key is provided.

Built with **FastAPI** and a clean HTML/CSS/JS dashboard.

## Features

- **Multi-format ingestion**: PDF (`pypdf`), DOCX (`python-docx`), TXT/MD.
- **Sentence-aware chunking** with overlap for better recall.
- **TF-IDF vector store** (uni+bi-grams, cosine similarity) — no model downloads, runs anywhere.
- **Cited answers**: every answer lists the source chunks with document name, page (PDFs), and similarity score.
- **Two answer modes**:
  - *Extractive* (default, offline): stitches together the best-matching sentences and highlights query terms.
  - *Generative*: sends retrieved context to an LLM for a fluent, cited answer.
- **Graceful fallback**: if the LLM is unavailable, it automatically falls back to extractive.
- Drag-and-drop UI with live knowledge-base stats and highlighted evidence.
