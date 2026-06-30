from __future__ import annotations

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import SERVER_HOST, SERVER_PORT
from .models import DialogueRequest, DialogueResponse
from .orchestrator import DialogueOrchestrator

app = FastAPI(title="Portfolio NPC RAG Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = DialogueOrchestrator()


@app.get("/api/v1/health")
def health() -> dict:
    return {"ok": True, "service": "portfolio-npc-rag-agent"}


@app.post("/api/v1/dialogue", response_model=DialogueResponse)
async def dialogue(req: DialogueRequest) -> DialogueResponse:
    try:
        return await orchestrator.handle(req)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"dialogue_failed: {e}")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=SERVER_HOST, port=SERVER_PORT, reload=True)
