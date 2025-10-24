from __future__ import annotations

import logging
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..config import get_settings
from ..agents.agent_client import get_agent_client, Message

logger = logging.getLogger("uvicorn")

app = FastAPI(title="Fiserv Payments Assistant")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    reply: str


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/")
def root():
    return {
        "app": "Fiserv Payments Assistant",
        "message": "Welcome. See /docs for Swagger UI.",
        "endpoints": {
            "GET /healthz": "Liveness probe",
            "POST /chat": "Chat with the payments assistant",
        },
        "docs": "/docs",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        agent = get_agent_client()
        msgs = [Message(role=m.role, content=m.content) for m in req.messages]
        reply = agent.chat(msgs)
        return ChatResponse(reply=reply)
    except Exception as ex:  # pragma: no cover - logged and returned as 500
        logger.exception("Chat failed: %s", ex)
        raise HTTPException(status_code=500, detail="Agent invocation failed")
