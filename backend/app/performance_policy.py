from __future__ import annotations

from collections import defaultdict, deque
from typing import Deque, Dict, List, Tuple

from .models import NormalizedDialogueResponse


PerformanceKey = Tuple[str, str, str]


class PerformanceActionPolicy:
    """Keeps optional NPC gestures varied without inventing mismatched actions."""

    _EXPLICIT_LAUGH_CUES = (
        "笑话",
        "好笑",
        "逗笑",
        "笑一个",
        "笑一下",
        "发笑",
        "轻笑",
        "哈哈",
        "呵呵",
    )

    def __init__(self, history_size: int = 4, soft_laugh_cooldown_turns: int = 2):
        self.history_size = max(1, history_size)
        self.soft_laugh_cooldown_turns = max(0, soft_laugh_cooldown_turns)
        self._actions: Dict[PerformanceKey, Deque[str]] = defaultdict(
            lambda: deque(maxlen=self.history_size)
        )

    def recent_actions(self, session_id: str, player_id: str, npc_id: str) -> List[str]:
        return list(self._actions[self._key(session_id, player_id, npc_id)])

    def apply(
        self,
        response: NormalizedDialogueResponse,
        session_id: str,
        player_id: str,
        npc_id: str,
        player_text: str,
    ) -> NormalizedDialogueResponse:
        key = self._key(session_id, player_id, npc_id)
        history = self._actions[key]

        if npc_id == "genshin_yae_miko" and not self._explicitly_requests_laughter(player_text):
            recent = (
                list(history)[-self.soft_laugh_cooldown_turns :]
                if self.soft_laugh_cooldown_turns
                else []
            )
            if "soft_laugh" in recent:
                for utterance in response.utterances:
                    if utterance.action == "soft_laugh":
                        utterance.action = "idle"

        performed_action = next(
            (utterance.action for utterance in response.utterances if utterance.action != "idle"),
            "idle",
        )
        history.append(performed_action)
        return response

    def reset_player(self, player_id: str) -> None:
        keys = [key for key in self._actions if key[1] == player_id]
        for key in keys:
            del self._actions[key]

    @classmethod
    def _explicitly_requests_laughter(cls, player_text: str) -> bool:
        return any(cue in player_text for cue in cls._EXPLICIT_LAUGH_CUES)

    @staticmethod
    def _key(session_id: str, player_id: str, npc_id: str) -> PerformanceKey:
        return session_id, player_id, npc_id
