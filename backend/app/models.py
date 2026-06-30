from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorldState(BaseModel):
    location_id: str = "portfolio_whitebox_room"
    game_time_label: str = "demo"
    quest_stage: int = 0
    relationship_score: float = 0.0
    debug_enabled: bool = False


class DialogueRequest(BaseModel):
    schema_version: str = "dialogue_request.v1"
    session_id: str
    player_id: str = "local_player"
    npc_id: str
    player_text: str
    distance_m: float = 0.0
    is_in_range: bool = True
    world_state: WorldState = Field(default_factory=WorldState)


class Utterance(BaseModel):
    text: str
    emotion: str = "neutral"
    action: str = "idle"
    delay_ms: int = 500


class InternalDebug(BaseModel):
    used_knowledge_ids: List[str] = Field(default_factory=list)
    used_memory_ids: List[str] = Field(default_factory=list)
    memory_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0


class DialogueResponse(BaseModel):
    schema_version: str = "dialogue_response.v1"
    turn_id: str
    npc_id: str
    utterances: List[Utterance]
    internal: InternalDebug = Field(default_factory=InternalDebug)


class RetrievedChunk(BaseModel):
    chunk_id: str
    title: str
    retrieval_text: str
    npc_sayable: List[str] = Field(default_factory=list)
    score: float = 0.0


class DebugRetrieveResponse(BaseModel):
    npc_id: str
    query: str
    quest_stage: int = 0
    max_spoiler_level: int = 1
    chunks: List[RetrievedChunk] = Field(default_factory=list)


class MemorySnippet(BaseModel):
    memory_id: str
    summary: str
    detail: str
    score: float = 0.0
