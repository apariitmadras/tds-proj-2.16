
from __future__ import annotations
import os, json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from starlette.datastructures import UploadFile
from lib.logging_config import get_logger
from lib.deadline import Deadline
from pipelines.orchestrator import run_pipeline

LOG = get_logger("app")
app = FastAPI(title="Data Analyst Agent — Multi‑Model Chain")

DEADLINE_SECONDS = float(os.getenv("DEADLINE_SECONDS", "285"))

@app.get("/", response_class=PlainTextResponse)
async def root():
    return "OK"

def _extract_files(form):
    files = {}
    for k, v in form.multi_items():
        if isinstance(v, UploadFile):
            files.setdefault(k, v)
    return files

async def _read_questions(form) -> str:
    if "questions.txt" not in form:
        present = [k for k, v in form.multi_items() if isinstance(v, UploadFile)]
        detail = "questions.txt is required; field name must be exactly 'questions.txt'. " \
                 f"Received file fields: {present}. " \
                 "Example: curl -F \"questions.txt=@question.txt\" https://<host>/api/"
        raise HTTPException(status_code=400, detail=detail)
    qf = form["questions.txt"]
    if not isinstance(qf, UploadFile):
        raise HTTPException(status_code=400, detail="questions.txt must be a file")
    data = await qf.read()
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        text = str(data)
    return text

@app.post("/api/", response_class=PlainTextResponse)
@app.post("/api/analyze", response_class=PlainTextResponse)
async def analyze(request: Request):
    deadline = Deadline(DEADLINE_SECONDS)
    form = await request.form()
    _ = _extract_files(form)  # collect attachments if needed
    prompt = await _read_questions(form)

    # Run the pipeline (guaranteed to return JSON string)
    json_text = run_pipeline(prompt, deadline)
    return json_text
