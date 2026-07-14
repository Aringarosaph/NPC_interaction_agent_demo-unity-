from __future__ import annotations

from app.models import NormalizedDialogueResponse, Utterance
from app.performance_history import PerformanceActionHistory


def _response(action: str) -> NormalizedDialogueResponse:
    return NormalizedDialogueResponse(
        turn_id="turn_test",
        npc_id="genshin_yae_miko",
        utterances=[Utterance(text="有点意思。", expression="amused", action=action)],
    )


def test_history_records_without_changing_model_action() -> None:
    history = PerformanceActionHistory()
    response = _response("soft_laugh")

    history.record(response, "session_a", "player_a", "genshin_yae_miko")
    history.record(response, "session_a", "player_a", "genshin_yae_miko")

    assert response.utterances[0].action == "soft_laugh"
    assert history.recent_actions("session_a", "player_a", "genshin_yae_miko") == [
        "soft_laugh",
        "soft_laugh",
    ]


def test_history_keeps_latest_ten_turns() -> None:
    history = PerformanceActionHistory()

    for index in range(12):
        action = "nod" if index == 0 else "idle"
        history.record(_response(action), "session_a", "player_a", "genshin_yae_miko")

    assert history.recent_actions("session_a", "player_a", "genshin_yae_miko") == [
        "idle"
    ] * 10


def test_history_is_isolated_and_reset_by_player() -> None:
    history = PerformanceActionHistory()
    history.record(_response("thoughtful"), "session_a", "player_a", "genshin_yae_miko")

    assert history.recent_actions("session_b", "player_a", "genshin_yae_miko") == []

    history.reset_player("player_a")
    assert history.recent_actions("session_a", "player_a", "genshin_yae_miko") == []
