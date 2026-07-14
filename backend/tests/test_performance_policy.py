from __future__ import annotations

from app.models import NormalizedDialogueResponse, Utterance
from app.performance_policy import PerformanceActionPolicy


def _response(action: str) -> NormalizedDialogueResponse:
    return NormalizedDialogueResponse(
        turn_id="turn_test",
        npc_id="genshin_yae_miko",
        utterances=[Utterance(text="有点意思。", expression="amused", action=action)],
    )


def _apply(policy: PerformanceActionPolicy, action: str, player_text: str = "说说你的看法"):
    return policy.apply(
        _response(action),
        session_id="session_a",
        player_id="player_a",
        npc_id="genshin_yae_miko",
        player_text=player_text,
    )


def test_soft_laugh_is_suppressed_during_two_turn_cooldown() -> None:
    policy = PerformanceActionPolicy()

    assert _apply(policy, "soft_laugh").utterances[0].action == "soft_laugh"
    assert _apply(policy, "soft_laugh").utterances[0].action == "idle"
    _apply(policy, "nod")
    assert _apply(policy, "soft_laugh").utterances[0].action == "soft_laugh"


def test_explicit_laughter_request_bypasses_cooldown() -> None:
    policy = PerformanceActionPolicy()
    _apply(policy, "soft_laugh")

    response = _apply(policy, "soft_laugh", player_text="这个笑话好笑吗？")

    assert response.utterances[0].action == "soft_laugh"


def test_recent_actions_are_isolated_and_reset_by_player() -> None:
    policy = PerformanceActionPolicy()
    _apply(policy, "thoughtful")

    assert policy.recent_actions("session_a", "player_a", "genshin_yae_miko") == [
        "thoughtful"
    ]
    assert policy.recent_actions("session_b", "player_a", "genshin_yae_miko") == []

    policy.reset_player("player_a")
    assert policy.recent_actions("session_a", "player_a", "genshin_yae_miko") == []
