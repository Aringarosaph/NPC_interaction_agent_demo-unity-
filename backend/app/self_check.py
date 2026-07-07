from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Sequence

from .models import DialogueRequest, NormalizedDialogueResponse, ToolResult, Utterance, WorldEvent


META_TERMS = ["AI", "模型", "Unity", "后端", "系统提示", "提示词", "知识库", "检索结果", "source_id"]
UNCERTAINTY_TERMS = [
    "无法确认",
    "不清楚",
    "不知道",
    "没有情报",
    "没有这份情报",
    "没有这项记录",
    "没有记录",
    "不了解",
    "无法判断",
    "难以确认",
]
SUCCESS_TERMS = ["完成", "开始", "记录好了", "已推进", "收下", "找回", "交付"]
QUEST_START_TERMS = ["任务开始", "委托开始", "请求开始", "已经开始"]
QUEST_COMPLETE_TERMS = ["任务完成", "委托完成", "请求完成", "已经完成"]

NPC_FORBIDDEN_TERMS = {
    "arknights_amiya": ["八重", "神子", "原神", "稻妻", "今汐", "鸣潮", "今州"],
    "genshin_yae_miko": ["阿米娅", "罗德岛", "明日方舟", "泰拉", "今汐", "鸣潮", "今州"],
    "wuwa_jinhsi": ["阿米娅", "罗德岛", "明日方舟", "八重", "神子", "原神", "稻妻"],
}


@dataclass(frozen=True)
class SelfCheckResult:
    passed: bool
    failure_reason: str | None = None
    corrective_hint: str | None = None


class ResponseSelfChecker:
    def check(
        self,
        profile: Dict[str, Any],
        request: DialogueRequest,
        response: NormalizedDialogueResponse,
        tool_results: Sequence[ToolResult],
        world_events: Sequence[WorldEvent],
        state_snapshot: Dict[str, Any],
    ) -> SelfCheckResult:
        texts = [utterance.text.strip() for utterance in response.utterances if utterance.text.strip()]
        if not 1 <= len(texts) <= 3:
            return self._fail("invalid_utterance_count", "将回复压缩为 1 到 3 句短句。")

        joined = "\n".join(texts)
        if self._has_markdown_list(texts):
            return self._fail("markdown_list_format", "不要使用列表或 Markdown 格式。")

        if any(term in joined for term in META_TERMS):
            return self._fail("implementation_leakage", "用角色内说法回避 AI、Unity、后端或系统提示。")

        if self._has_cross_world_leakage(request.npc_id, joined):
            return self._fail("cross_world_leakage", "不要给出其他作品世界的确定性知识。")

        if any(not result.ok for result in tool_results) and self._sounds_successful(joined):
            return self._fail("failed_tool_described_as_success", "工具失败时不要描述为成功。")

        if self._contradicts_quest_state(joined, world_events, state_snapshot):
            return self._fail("quest_state_contradiction", "不要宣称未发生的任务状态变化。")

        return SelfCheckResult(True)

    def fallback_utterance(self, profile: Dict[str, Any], result: SelfCheckResult) -> Utterance:
        text = "这件事我还需要再确认。"
        npc_id = profile.get("npc_id")
        if result.failure_reason == "cross_world_leakage":
            text = "这件事我无法确认。"
        elif npc_id == "genshin_yae_miko":
            text = "呵，这事还得再斟酌。"
        elif npc_id == "wuwa_jinhsi":
            text = "此事仍需再核实。"
        return Utterance(text=text, emotion="neutral", action="idle", delay_ms=500)

    @staticmethod
    def reflection(result: SelfCheckResult) -> Dict[str, str] | None:
        if result.passed:
            return None
        return {
            "failure_reason": result.failure_reason or "unknown",
            "corrective_hint": result.corrective_hint or "Use a conservative in-character fallback.",
        }

    @staticmethod
    def _fail(reason: str, hint: str) -> SelfCheckResult:
        return SelfCheckResult(False, failure_reason=reason, corrective_hint=hint)

    @staticmethod
    def _has_markdown_list(texts: Iterable[str]) -> bool:
        return any(re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", text) for text in texts)

    @staticmethod
    def _has_cross_world_leakage(npc_id: str, text: str) -> bool:
        forbidden_terms = NPC_FORBIDDEN_TERMS.get(npc_id, [])
        if not any(term in text for term in forbidden_terms):
            return False
        return not any(term in text for term in UNCERTAINTY_TERMS)

    @staticmethod
    def _sounds_successful(text: str) -> bool:
        if any(term in text for term in UNCERTAINTY_TERMS + ["失败", "不能", "还没有", "尚未"]):
            return False
        return any(term in text for term in SUCCESS_TERMS)

    @staticmethod
    def _contradicts_quest_state(
        text: str,
        world_events: Sequence[WorldEvent],
        state_snapshot: Dict[str, Any],
    ) -> bool:
        event_types = {event.event_type for event in world_events}
        quest_states = state_snapshot.get("quests", [])
        has_active_or_completed = any(
            quest.get("status") in {"active", "completed"} for quest in quest_states
        )
        if any(term in text for term in QUEST_START_TERMS) and "quest_started" not in event_types and not has_active_or_completed:
            return True
        if any(term in text for term in QUEST_COMPLETE_TERMS) and "quest_advanced" not in event_types:
            return True
        return False
