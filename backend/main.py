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
