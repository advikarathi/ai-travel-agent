"""Lark's trip desk.

    .\\.venv\\Scripts\\python.exe -m uvicorn server:app --reload --port 8765
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from lark.agent import respond
from lark.llm import LLMError

ROOT = Path(__file__).resolve().parent


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv()

app = FastAPI(title="Lark")


class ChatIn(BaseModel):
    message: str = ""
    state: dict | None = Field(default=None)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "name": "Lark"}


@app.post("/api/chat")
def chat(body: ChatIn) -> dict:
    try:
        return respond(body.message, body.state)
    except LLMError as error:
        # Missing key, rate limit, provider down: say so instead of a 500.
        return {"reply": str(error), "state": body.state, "plan": None, "suggestions": [], "status": "error"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
