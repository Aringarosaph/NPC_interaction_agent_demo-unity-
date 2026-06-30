from __future__ import annotations

from typing import Any, Dict, List
from .models import DialogueResponse, InternalDebug, Utterance

ALLOWED_EMOTIONS = {"neutral", "warm", "concerned", "resolute", "teasing", "amused", "solemn", "distant", "cautious", "gentle"}
ALLOWED_ACTIONS = {"idle", "nod", "look_at_player", "small_smile", "sigh", "turn_away", "thoughtful", "bow", "hand_on_chest"}


class ResponseNormalizer:
    def normalize(self, raw: Dict[str, Any], npc_id: str, turn_id: str, sentence_max_chars: int = 28, max_utterances: int = 3) -> DialogueResponse:
        utterances: List[Utterance] = []
        for item in raw.get("utterances", [])[:max_utterances]:
            text = str(item.get("text", "")).strip()
            if not text:
                continue
            text = self._trim_sentence(text, sentence_max_chars)
            emotion = item.get("emotion", "neutral")
            action = item.get("action", "idle")
            utterances.append(Utterance(
                text=text,
                emotion=emotion if emotion in ALLOWED_EMOTIONS else "neutral",
                action=action if action in ALLOWED_ACTIONS else "idle",
                delay_ms=int(item.get("delay_ms", 500)),
            ))
        if not utterances:
            utterances = [Utterance(text="这件事我无法确认。", emotion="neutral", action="idle", delay_ms=500)]
        return DialogueResponse(
            turn_id=turn_id,
            npc_id=npc_id,
            utterances=utterances,
            internal=InternalDebug(
                used_knowledge_ids=list(raw.get("used_knowledge_ids", [])),
                used_memory_ids=list(raw.get("used_memory_ids", [])),
                memory_candidates=list(raw.get("memory_candidates", [])),
                confidence=float(raw.get("confidence", 0.0)),
            ),
        )

    @staticmethod
    def _trim_sentence(text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        for sep in ["。", "！", "？"]:
            idx = text.find(sep)
            if 0 < idx <= max_chars:
                return text[: idx + 1]
        # A comma clause is better than a hard cut, but do not leave the bubble
        # hanging on a trailing comma.
        for sep in ["，", ",", ";", "；"]:
            idx = text.find(sep)
            if 0 < idx <= max_chars:
                return text[:idx]
        return text[:max_chars]
