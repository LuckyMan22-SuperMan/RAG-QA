"""FastAPI backend for the RAG Document Q&A app.

Endpoints:
    GET  /api/health   -> health + LLM availability
    GET  /api/status   -> indexed documents / chunk counts
    POST /api/ingest   -> upload one or more files (multipart), index them
    POST /api/ask      -> ask a question over the indexed corpus
    POST /api/reset    -> clear the index

Serves the static frontend from ../static at "/".
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend import ingest
# import backend.ingest
from backend import llm
from backend import rag
from backend.store import store

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="RAG Document Q&A", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "llm": llm.info()}


@app.get("/api/status")
def status() -> dict:
    return {**store.stats(), "llm": llm.info()}


@app.post("/api/ingest")
async def ingest_files(files: List[UploadFile] = File(...)) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    added = []
    errors = []
    for f in files:
        data = await f.read()
        try:
            start_id = store.stats()["num_chunks"]
            doc = ingest.build_document(f.filename, data, start_id=start_id)
            store.add_chunks(doc.chunks)
            added.append({"name": f.filename, "chunks": len(doc.chunks)})
        except Exception as exc:  # noqa: BLE001
            errors.append({"name": f.filename, "error": str(exc)})
    if not added and errors:
        raise HTTPException(status_code=400, detail=errors[0]["error"])
    return {"added": added, "errors": errors, "status": store.stats()}


@app.post("/api/ask")
def ask(question: str = Form(...), top_k: int = Form(5),
        mode: str = Form("auto")) -> dict:
    try:
        return rag.answer(question, top_k=top_k, mode=mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/remove")
def remove(name: str = Form(...)) -> dict:
    if not store.remove_document(name):
        raise HTTPException(status_code=404, detail=f"Document '{name}' not indexed.")
    return {"removed": name, "status": store.stats()}


@app.post("/api/reset")
def reset() -> dict:
    store.reset()
    return {"status": store.stats()}


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(str(STATIC_DIR / "index.html"))
