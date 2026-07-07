from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class WorldState(BaseModel):
    location_id: str = "portfolio_whitebox_room"
    game_time_label: str = "demo"
    quest_stage: int = 0
    relationship_score: float = 0.0
    debug_enabled: bool = False


class DialogueRequest(BaseModel):
    schema_version: str = "dialogue_request.agent"
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


class NormalizedDialogueResponse(BaseModel):
    schema_version: str = "dialogue_response.internal"
    turn_id: str
    npc_id: str
    utterances: List[Utterance]
    internal: InternalDebug = Field(default_factory=InternalDebug)


class AgentPlan(BaseModel):
    intent: str
    goal: str
    required_knowledge: List[str] = Field(default_factory=list)
    proposed_tools: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    public_reason: str


class ToolCall(BaseModel):
    call_id: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    reason: str


class ToolResult(BaseModel):
    call_id: str
    tool_name: str
    ok: bool
    result: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class WorldEvent(BaseModel):
    event_id: str
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    player_visible: bool = True


class AgentTrace(BaseModel):
    used_knowledge_ids: List[str] = Field(default_factory=list)
    used_memory_ids: List[str] = Field(default_factory=list)
    plan: Optional[AgentPlan] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tool_results: List[ToolResult] = Field(default_factory=list)
    memory_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    reflection: Optional[Dict[str, Any]] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class AgentDialogueResponse(BaseModel):
    schema_version: Literal["dialogue_response.agent"] = "dialogue_response.agent"
    turn_id: str
    npc_id: str
    utterances: List[Utterance]
    world_events: List[WorldEvent] = Field(default_factory=list)
    trace: AgentTrace = Field(default_factory=AgentTrace)


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


class MemoryDebugRecord(BaseModel):
    memory_id: str
    npc_id: str
    player_id: str
    memory_type: str
    summary: str
    detail: str
    salience: float
    confidence: float
    created_at: str
    last_seen_at: str
    decay_policy: str
    expires_at: Optional[str] = None
    source_turn_id: Optional[str] = None
    write_protected: bool = False
    visibility: Dict[str, Any] = Field(default_factory=dict)
    retrieval_keywords: List[str] = Field(default_factory=list)
    status: str


class DebugMemoriesResponse(BaseModel):
    npc_id: str
    player_id: str
    include_default: bool = True
    include_superseded: bool = False
    memories: List[MemoryDebugRecord] = Field(default_factory=list)
