from __future__ import annotations

import uuid
from typing import Any, Dict, List, Sequence

from .models import AgentPlan, DialogueRequest, MemorySnippet, RetrievedChunk, ToolCall
from .tools import ToolSpec


DEFAULT_AGENT_QUEST_ID = "shared_field_request"


class AgentPlanner:
    def plan(
        self,
        profile: Dict[str, Any],
        request: DialogueRequest,
        retrieved_chunks: Sequence[RetrievedChunk],
        memories: Sequence[MemorySnippet],
        state_snapshot: Dict[str, Any],
        tool_specs: Sequence[ToolSpec],
        turn_id: str,
    ) -> tuple[AgentPlan, List[ToolCall]]:
        available_tools = {spec.name for spec in tool_specs}
        text = request.player_text.strip()
        quest = self._quest_state(state_snapshot, DEFAULT_AGENT_QUEST_ID)
        required_knowledge = [chunk.chunk_id for chunk in retrieved_chunks]
        memory_ids = [memory.memory_id for memory in memories]

        calls: List[ToolCall] = []
        intent = "answer"
        goal = "Answer the player while staying in character."
        risk_flags: List[str] = []
        public_reason = "玩家只是继续对话，因此不需要改变世界状态。"

        if self._is_accepting_task(text) and quest.get("status") in {None, "not_started"}:
            intent = "start_quest"
            goal = "Start the current lightweight NPC request after the player agrees to help."
            public_reason = "玩家明确表示愿意帮忙，可以开启当前请求。"
            calls.append(self._call(turn_id, "start_quest", {"quest_id": DEFAULT_AGENT_QUEST_ID}, public_reason))
        elif self._is_completing_task(text) and quest.get("status") == "active":
            intent = "complete_quest"
            goal = "Advance the active request and reward the player's helpful action."
            public_reason = "玩家表示已经找回或交付任务物品，可以推进任务并提高关系。"
            calls.append(
                self._call(
                    turn_id,
                    "advance_quest",
                    {"quest_id": DEFAULT_AGENT_QUEST_ID, "expected_stage": int(quest.get("stage", 1))},
                    "玩家提交了当前请求的关键物品或结果。",
                )
            )
            calls.append(
                self._call(
                    turn_id,
                    "update_relationship",
                    {"delta": 6, "reason": "玩家完成了当前请求。"},
                    "完成请求后提高 NPC 对玩家的信任。",
                )
            )
        elif self._is_preference_memory(text):
            intent = "remember_preference"
            goal = "Let the existing memory extraction path store the player's address preference."
            public_reason = "玩家提供了称呼偏好，交给记忆策略处理，不需要工具调用。"

        calls = [call for call in calls if call.tool_name in available_tools]
        if intent in {"start_quest", "complete_quest"} and not calls:
            risk_flags.append("planned_tool_missing")
            public_reason = "需要的工具当前不可用，因此不改变世界状态。"

        plan = AgentPlan(
            intent=intent,
            goal=goal,
            required_knowledge=required_knowledge + memory_ids,
            proposed_tools=[call.tool_name for call in calls],
            risk_flags=risk_flags,
            public_reason=public_reason,
        )
        return plan, calls

    @staticmethod
    def _call(turn_id: str, tool_name: str, arguments: Dict[str, Any], reason: str) -> ToolCall:
        return ToolCall(
            call_id=f"call_{turn_id}_{uuid.uuid4().hex[:8]}",
            tool_name=tool_name,
            arguments=arguments,
            reason=reason,
        )

    @staticmethod
    def _quest_state(state_snapshot: Dict[str, Any], quest_id: str) -> Dict[str, Any]:
        for quest in state_snapshot.get("quests", []):
            if quest.get("quest_id") == quest_id:
                return quest
        return {"quest_id": quest_id, "stage": 0, "status": "not_started"}

    @staticmethod
    def _is_accepting_task(text: str) -> bool:
        return any(word in text for word in ["接受", "愿意", "帮你", "我来", "交给我", "可以帮", "我帮"])

    @staticmethod
    def _is_completing_task(text: str) -> bool:
        return any(word in text for word in ["找到了", "找回", "给你", "带来了", "完成", "徽章"])

    @staticmethod
    def _is_preference_memory(text: str) -> bool:
        return "叫我" in text or "称呼我" in text
