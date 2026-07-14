from __future__ import annotations

from collections import defaultdict, deque
from typing import Deque, Dict, List, Tuple

from .models import NormalizedDialogueResponse


PerformanceKey = Tuple[str, str, str]


class PerformanceActionHistory:
    """Remembers final actions for prompt context without changing model output."""

    def __init__(self, history_size: int = 10):
        self.history_size = max(1, history_size)
        self._actions: Dict[PerformanceKey, Deque[str]] = defaultdict(
            lambda: deque(maxlen=self.history_size)
        )

    def recent_actions(self, session_id: str, player_id: str, npc_id: str) -> List[str]:
        actions = self._actions.get(self._key(session_id, player_id, npc_id))
        return list(actions) if actions is not None else []

    def record(
        self,
        response: NormalizedDialogueResponse,
        session_id: str,
        player_id: str,
        npc_id: str,
    ) -> None:
        performed_action = next(
            (utterance.action for utterance in response.utterances if utterance.action != "idle"),
            "idle",
        )
        self._actions[self._key(session_id, player_id, npc_id)].append(performed_action)

    def reset_player(self, player_id: str) -> None:
        keys = [key for key in self._actions if key[1] == player_id]
        for key in keys:
            del self._actions[key]

    @staticmethod
    def _key(session_id: str, player_id: str, npc_id: str) -> PerformanceKey:
        return session_id, player_id, npc_id
