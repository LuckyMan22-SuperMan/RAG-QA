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

## Architecture

```
rag-qa/
├── backend/
│   ├── main.py      # FastAPI endpoints, serves the frontend
│   ├── ingest.py    # text extraction + sentence-aware chunking
│   ├── store.py     # TF-IDF vector store (fit / search / reset)
│   ├── rag.py       # retrieve + extractive answer + optional LLM
│   └── llm.py       # optional OpenAI-compatible client
├── static/          # index.html, style.css, app.js
├── requirements.txt
└── README.md
```

## Setup

### Windows
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python backend/main.py
```

### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python backend/main.py
```

Open http://127.0.0.1:8000  (set `PORT` to change the port).

## Enabling the optional LLM

The app runs offline by default (extractive answers). To enable generative answers,
set environment variables before starting the server:

```bash
export OPENAI_API_KEY=sk-...            # required to enable the LLM
export OPENAI_MODEL=gpt-4o-mini         # optional (default)
export OPENAI_BASE_URL=https://api.openai.com/v1   # optional
python backend/main.py
```

It's OpenAI-compatible, so you can also point it at a **local** model server
(e.g. Ollama: `OPENAI_BASE_URL=http://localhost:11434/v1`, `OPENAI_MODEL=llama3`).

> Never hard-code API keys. Use environment variables as shown above.

## API

| Method | Endpoint       | Body                              | Returns                       |
|--------|----------------|-----------------------------------|-------------------------------|
| GET    | `/api/health`  | —                                 | status + LLM info             |
| GET    | `/api/status`  | —                                 | indexed docs + chunk counts   |
| POST   | `/api/ingest`  | `files` (multipart, 1+)           | added docs + errors           |
| POST   | `/api/ask`     | `question`, `top_k`, `mode`       | answer + cited sources        |
| POST   | `/api/reset`   | —                                 | cleared status                |

## How RAG works here

1. **Ingest**: extract text -> clean -> split into overlapping sentence chunks.
2. **Index**: fit a TF-IDF matrix over all chunks.
3. **Retrieve**: embed the question with the same vectorizer, rank chunks by cosine similarity, take top-k.
4. **Answer**: extractive (pick best sentences, cite chunks) or generative (LLM over the retrieved context).

## Ideas to extend (interview talking points)

- Swap TF-IDF for **dense embeddings** (sentence-transformers) + **FAISS**; keep the same `store` interface.
- Add a **re-ranker** (cross-encoder) over the top-k for better precision.
- Persist the index (SQLite/`joblib`) so it survives restarts.
- Add **conversation memory** for follow-up questions and streaming responses.
- Show **retrieval metrics** (recall@k) on a labeled eval set.

## Notes

- First run installs `scikit-learn`/`scipy` which are moderately large.
- Everything is in-memory; restarting the server clears the knowledge base.
