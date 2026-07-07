from __future__ import annotations

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import SERVER_HOST, SERVER_PORT
from .models import AgentDialogueResponse, DialogueRequest, DebugRetrieveResponse, DebugMemoriesResponse
from .orchestrator import DialogueOrchestrator

app = FastAPI(title="Portfolio NPC RAG Agent", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = DialogueOrchestrator()


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "service": "portfolio-npc-rag-agent"}


@app.post("/api/dialogue", response_model=AgentDialogueResponse)
async def dialogue(req: DialogueRequest) -> AgentDialogueResponse:
    try:
        return await orchestrator.handle(req)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"dialogue_failed: {e}")


@app.get("/api/debug/retrieve", response_model=DebugRetrieveResponse)
def debug_retrieve(
    npc_id: str = Query(..., min_length=1),
    q: str = Query(..., min_length=1),
    quest_stage: int = 0,
    max_spoiler_level: int | None = None,
) -> DebugRetrieveResponse:
    try:
        return orchestrator.debug_retrieve(
            npc_id=npc_id,
            query=q,
            quest_stage=quest_stage,
            max_spoiler_level=max_spoiler_level,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"debug_retrieve_failed: {e}")


@app.get("/api/debug/memories", response_model=DebugMemoriesResponse)
def debug_memories(
    npc_id: str = Query(..., min_length=1),
    player_id: str = Query("local_player", min_length=1),
    include_default: bool = True,
    include_superseded: bool = False,
) -> DebugMemoriesResponse:
    try:
        return orchestrator.debug_memories(
            npc_id=npc_id,
            player_id=player_id,
            include_default=include_default,
            include_superseded=include_superseded,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"debug_memories_failed: {e}")


@app.post("/api/debug/reset")
def debug_reset_demo_state(player_id: str = Query("local_player", min_length=1)) -> dict:
    try:
        return orchestrator.reset_demo_state(player_id=player_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"debug_reset_failed: {e}")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=SERVER_HOST, port=SERVER_PORT, reload=True)
