from __future__ import annotations

import re
import uuid
import json
from typing import Dict, List

from .data_loader import DataLoader
from .retriever import SmallKnowledgeRetriever
from .memory_store import MemoryStore
from .state_store import StateStore
from .prompt_builder import PromptBuilder
from .llm_client import LlmClient
from .response_normalizer import ResponseNormalizer
from .agent_planner import AgentPlanner
from .models import (
    AgentTrace,
    DebugMemoriesResponse,
    DebugRetrieveResponse,
    DialogueRequest,
    DialogueResponse,
    DialogueResponseV2,
    InternalDebug,
    ToolResult,
    Utterance,
    WorldEvent,
)
from .tools import ToolExecutionContext, ToolRegistry, create_default_registry
from .config import CONFIG


class DialogueOrchestrator:
    def __init__(
        self,
        memory_store: MemoryStore | None = None,
        llm: LlmClient | None = None,
        state_store: StateStore | None = None,
        tool_registry: ToolRegistry | None = None,
        planner: AgentPlanner | None = None,
    ):
        self.loader = DataLoader()
        bundles = self.loader.load_all()
        self.bundles = bundles
        self.retriever = SmallKnowledgeRetriever(
            {npc_id: bundle.chunks for npc_id, bundle in bundles.items()},
            top_k=CONFIG.get("retrieval", {}).get("top_k", 4),
            min_score=CONFIG.get("retrieval", {}).get("min_score", 0.035),
        )
        self.memory_store = memory_store or MemoryStore()
        for b in bundles.values():
            self.memory_store.seed_from_pack(b.memory_seed)
        self.state_store = state_store or StateStore()
        self.tool_registry = tool_registry or create_default_registry(self.state_store)
        self.agent_planner = planner or AgentPlanner()
        self.prompt_builder = PromptBuilder()
        self.llm = llm or LlmClient()
        self.normalizer = ResponseNormalizer()

    async def handle(self, req: DialogueRequest) -> DialogueResponse:
        bundle = self.loader.get_bundle(req.npc_id)
        if not req.is_in_range:
            return DialogueResponse(
                turn_id=f"turn_{uuid.uuid4().hex[:12]}",
                npc_id=req.npc_id,
                utterances=[
                    Utterance(text="请再靠近一些。", emotion="neutral", action="idle", delay_ms=300)
                ],
                internal=InternalDebug(confidence=1.0),
            )
        profile = bundle.profile
        turn_id = f"turn_{uuid.uuid4().hex[:12]}"
        chunks = self.retriever.retrieve(
            npc_id=req.npc_id,
            query=req.player_text,
            quest_stage=req.world_state.quest_stage,
            max_spoiler_level=profile.get("knowledge_policy", {}).get("max_spoiler_level_default", 1),
        )
        memories = self.memory_store.search(req.npc_id, req.player_id, req.player_text, limit=CONFIG.get("retrieval", {}).get("memory_top_k", 3))
        messages = self.prompt_builder.build(profile, req, chunks, memories)
        raw = await self.llm.generate_json(
            messages,
            temperature=profile.get("generation_policy", {}).get("llm_temperature", 0.5),
            max_tokens=profile.get("generation_policy", {}).get("max_tokens", 360),
            fallback_name=profile.get("display_name_zh", "NPC"),
        )
        deterministic_memory_candidates = self._extract_memory_candidates(req, turn_id)
        if deterministic_memory_candidates:
            raw["memory_candidates"] = deterministic_memory_candidates
        raw["used_knowledge_ids"] = self._trusted_ids(
            raw.get("used_knowledge_ids", []),
            [c.chunk_id for c in chunks],
        )
        raw["used_memory_ids"] = self._trusted_ids(
            raw.get("used_memory_ids", []),
            [m.memory_id for m in memories],
        )
        response = self.normalizer.normalize(
            raw,
            npc_id=req.npc_id,
            turn_id=turn_id,
            sentence_max_chars=profile.get("speech", {}).get("sentence_max_chars", 28),
            max_utterances=profile.get("generation_policy", {}).get("max_response_utterances", 3),
        )
        # MVP: write only explicit candidates returned by the model. Add stronger filtering in Phase 4.
        for candidate in response.internal.memory_candidates:
            self.memory_store.write_candidate(req.npc_id, req.player_id, candidate, source_turn_id=turn_id)
        return response

    async def handle_v2(self, req: DialogueRequest) -> DialogueResponseV2:
        bundle = self.loader.get_bundle(req.npc_id)
        turn_id = f"turn_{uuid.uuid4().hex[:12]}"
        if not req.is_in_range:
            return DialogueResponseV2(
                turn_id=turn_id,
                npc_id=req.npc_id,
                utterances=[
                    Utterance(text="请再靠近一些。", emotion="neutral", action="idle", delay_ms=300)
                ],
                trace=AgentTrace(confidence=1.0),
            )

        profile = bundle.profile
        chunks = self.retriever.retrieve(
            npc_id=req.npc_id,
            query=req.player_text,
            quest_stage=req.world_state.quest_stage,
            max_spoiler_level=profile.get("knowledge_policy", {}).get("max_spoiler_level_default", 1),
        )
        memories = self.memory_store.search(
            req.npc_id,
            req.player_id,
            req.player_text,
            limit=CONFIG.get("retrieval", {}).get("memory_top_k", 3),
        )
        state_snapshot = self.state_store.get_player_snapshot(req.player_id, req.npc_id)
        plan, tool_calls = self.agent_planner.plan(
            profile=profile,
            request=req,
            retrieved_chunks=chunks,
            memories=memories,
            state_snapshot=state_snapshot,
            tool_specs=self.tool_registry.list_specs(),
            turn_id=turn_id,
        )

        context = ToolExecutionContext(
            npc_id=req.npc_id,
            player_id=req.player_id,
            session_id=req.session_id,
            turn_id=turn_id,
        )
        tool_results: List[ToolResult] = []
        world_events: List[WorldEvent] = []
        for call in tool_calls:
            execution = self.tool_registry.execute(call.tool_name, call.arguments, context)
            tool_result = ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                ok=execution.ok,
                result=execution.result,
                error=execution.error,
            )
            tool_results.append(tool_result)
            event = self._world_event_from_tool_result(tool_result)
            if event is not None:
                world_events.append(event)

        messages = self._build_v2_messages(
            profile=profile,
            req=req,
            chunks=chunks,
            memories=memories,
            state_snapshot=state_snapshot,
            plan=plan.model_dump(),
            tool_results=[result.model_dump() for result in tool_results],
        )
        raw = await self.llm.generate_json(
            messages,
            temperature=profile.get("generation_policy", {}).get("llm_temperature", 0.5),
            max_tokens=profile.get("generation_policy", {}).get("max_tokens", 360),
            fallback_name=profile.get("display_name_zh", "NPC"),
        )
        deterministic_memory_candidates = self._extract_memory_candidates(req, turn_id)
        if deterministic_memory_candidates:
            raw["memory_candidates"] = deterministic_memory_candidates
        raw["used_knowledge_ids"] = self._trusted_ids(
            raw.get("used_knowledge_ids", []),
            [c.chunk_id for c in chunks],
        )
        raw["used_memory_ids"] = self._trusted_ids(
            raw.get("used_memory_ids", []),
            [m.memory_id for m in memories],
        )
        response_v1 = self.normalizer.normalize(
            raw,
            npc_id=req.npc_id,
            turn_id=turn_id,
            sentence_max_chars=profile.get("speech", {}).get("sentence_max_chars", 28),
            max_utterances=profile.get("generation_policy", {}).get("max_response_utterances", 3),
        )
        for candidate in response_v1.internal.memory_candidates:
            self.memory_store.write_candidate(req.npc_id, req.player_id, candidate, source_turn_id=turn_id)

        return DialogueResponseV2(
            turn_id=turn_id,
            npc_id=req.npc_id,
            utterances=response_v1.utterances,
            world_events=world_events,
            trace=AgentTrace(
                used_knowledge_ids=response_v1.internal.used_knowledge_ids,
                used_memory_ids=response_v1.internal.used_memory_ids,
                plan=plan,
                tool_calls=tool_calls,
                tool_results=tool_results,
                memory_candidates=response_v1.internal.memory_candidates,
                confidence=response_v1.internal.confidence,
            ),
        )

    def debug_retrieve(
        self,
        npc_id: str,
        query: str,
        quest_stage: int = 0,
        max_spoiler_level: int | None = None,
    ) -> DebugRetrieveResponse:
        bundle = self.loader.get_bundle(npc_id)
        profile = bundle.profile
        spoiler_level = (
            profile.get("knowledge_policy", {}).get("max_spoiler_level_default", 1)
            if max_spoiler_level is None
            else max_spoiler_level
        )
        chunks = self.retriever.retrieve(
            npc_id=npc_id,
            query=query,
            quest_stage=quest_stage,
            max_spoiler_level=spoiler_level,
        )
        return DebugRetrieveResponse(
            npc_id=npc_id,
            query=query,
            quest_stage=quest_stage,
            max_spoiler_level=spoiler_level,
            chunks=chunks,
        )

    def debug_memories(self, npc_id: str, player_id: str, include_default: bool = True) -> DebugMemoriesResponse:
        self.loader.get_bundle(npc_id)
        memories = self.memory_store.list_records(
            npc_id=npc_id,
            player_id=player_id,
            include_default=include_default,
        )
        return DebugMemoriesResponse(
            npc_id=npc_id,
            player_id=player_id,
            include_default=include_default,
            memories=memories,
        )

    @staticmethod
    def _trusted_ids(model_ids: List[str], backend_ids: List[str]) -> List[str]:
        trusted = [item for item in model_ids if item in backend_ids]
        return trusted or backend_ids

    def _build_v2_messages(
        self,
        profile: Dict[str, object],
        req: DialogueRequest,
        chunks: List[object],
        memories: List[object],
        state_snapshot: Dict[str, object],
        plan: Dict[str, object],
        tool_results: List[Dict[str, object]],
    ) -> List[Dict[str, str]]:
        messages = self.prompt_builder.build(profile, req, chunks, memories)
        messages[-1]["content"] += "\n\n<AGENT_STATE>\n"
        messages[-1]["content"] += json.dumps(state_snapshot, ensure_ascii=False, indent=2)
        messages[-1]["content"] += "\n</AGENT_STATE>\n\n<AGENT_PLAN>\n"
        messages[-1]["content"] += json.dumps(plan, ensure_ascii=False, indent=2)
        messages[-1]["content"] += "\n</AGENT_PLAN>\n\n<TOOL_RESULTS>\n"
        messages[-1]["content"] += json.dumps(tool_results, ensure_ascii=False, indent=2)
        messages[-1]["content"] += "\n</TOOL_RESULTS>"
        return messages

    @staticmethod
    def _world_event_from_tool_result(tool_result: ToolResult) -> WorldEvent | None:
        event = tool_result.result.get("world_event") if tool_result.ok else None
        if not isinstance(event, dict):
            return None
        return WorldEvent(
            event_id=str(event.get("event_id", "")),
            event_type=str(event.get("event_type", "")),
            payload=dict(event.get("payload", {})),
            player_visible=bool(event.get("player_visible", True)),
        )

    def _extract_memory_candidates(self, req: DialogueRequest, turn_id: str) -> List[Dict[str, object]]:
        preferred_name = self._extract_preferred_name(req.player_text)
        if not preferred_name:
            return []
        return [
            {
                "memory_id": f"mem_{req.npc_id}_{self._safe_id(req.player_id)}_preferred_address",
                "memory_type": "preference",
                "summary": f"玩家希望被称呼为{preferred_name}",
                "detail": f"玩家明确要求 NPC 以后称呼自己为{preferred_name}。",
                "salience": 0.92,
                "retrieval_keywords": ["称呼", "叫我", "记得", preferred_name, "玩家名字"],
                "source_turn_id": turn_id,
            }
        ]

    @staticmethod
    def _extract_preferred_name(player_text: str) -> str | None:
        if "怎么叫我" in player_text or "如何叫我" in player_text:
            return None
        patterns = [
            r"(?:以后|之后|接下来|下次)(?:请)?(?:叫|称呼)我(?:为|作|做)?([A-Za-z0-9_\u4e00-\u9fff]{1,12})",
            r"请(?:叫|称呼)我(?:为|作|做)?([A-Za-z0-9_\u4e00-\u9fff]{1,12})",
            r"^(?:叫|称呼)我(?:为|作|做)?([A-Za-z0-9_\u4e00-\u9fff]{1,12})",
        ]
        for pattern in patterns:
            match = re.search(pattern, player_text)
            if not match:
                continue
            name = match.group(1).strip()
            if name in {"吗", "嘛", "呢", "么", "什么", "谁"}:
                continue
            return name
        return None

    @staticmethod
    def _safe_id(value: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
        return safe[:40] or "player"
