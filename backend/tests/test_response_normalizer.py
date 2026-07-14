from __future__ import annotations

import unittest

from app.response_normalizer import ResponseNormalizer


class ResponseNormalizerPerformanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.normalizer = ResponseNormalizer()

    def test_keeps_supported_yae_performance_and_limits_action_to_one(self) -> None:
        response = self.normalizer.normalize(
            {
                "utterances": [
                    {"text": "哎呀，真直接。", "expression": "teasing", "action": "dismissive"},
                    {"text": "倒也有趣。", "expression": "amused", "action": "soft_laugh"},
                ]
            },
            npc_id="genshin_yae_miko",
            turn_id="turn_performance",
        )

        self.assertEqual(response.utterances[0].expression, "teasing")
        self.assertEqual(response.utterances[0].action, "dismissive")
        self.assertEqual(response.utterances[1].expression, "amused")
        self.assertEqual(response.utterances[1].action, "idle")

    def test_invalid_yae_performance_falls_back(self) -> None:
        response = self.normalizer.normalize(
            {"utterances": [{"text": "请继续。", "expression": "furious", "action": "dance"}]},
            npc_id="genshin_yae_miko",
            turn_id="turn_fallback",
        )

        self.assertEqual(response.utterances[0].expression, "neutral")
        self.assertEqual(response.utterances[0].action, "idle")

    def test_other_npcs_cannot_request_unavailable_performance(self) -> None:
        response = self.normalizer.normalize(
            {"utterances": [{"text": "我明白了。", "expression": "soft_smile", "action": "nod"}]},
            npc_id="arknights_amiya",
            turn_id="turn_no_performance",
        )

        self.assertEqual(response.utterances[0].expression, "neutral")
        self.assertEqual(response.utterances[0].action, "idle")


if __name__ == "__main__":
    unittest.main()
