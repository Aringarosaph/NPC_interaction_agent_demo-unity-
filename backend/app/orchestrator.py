from __future__ import annotations

import uuid
from typing import Dict, List

from .data_loader import DataLoader
from .retriever import SmallKnowledgeRetriever
from .memory_store import MemoryStore
from .prompt_builder import PromptBuilder
from .llm_client import LlmClient
from .response_normalizer import ResponseNormalizer
from .models import DialogueRequest, DialogueResponse, Utterance, InternalDebug, DebugRetrieveResponse
from .config import CONFIG


class DialogueOrchestrator:
    def __init__(self):
        self.loader = DataLoader()
        bundles = self.loader.load_all()
        self.bundles = bundles
        self.retriever = SmallKnowledgeRetriever(
            {npc_id: bundle.chunks for npc_id, bundle in bundles.items()},
            top_k=CONFIG.get("retrieval", {}).get("top_k", 4),
            min_score=CONFIG.get("retrieval", {}).get("min_score", 0.035),
        )
        self.memory_store = MemoryStore()
        for b in bundles.values():
            self.memory_store.seed_from_pack(b.memory_seed)
        self.prompt_builder = PromptBuilder()
        self.llm = LlmClient()
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
        # If model forgets IDs, fill retrieval IDs for debug.
        if not raw.get("used_knowledge_ids"):
            raw["used_knowledge_ids"] = [c.chunk_id for c in chunks]
        if not raw.get("used_memory_ids"):
            raw["used_memory_ids"] = [m.memory_id for m in memories]
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
