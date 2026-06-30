from __future__ import annotations

import os
import unittest
import warnings

os.environ.setdefault("MOCK_LLM_WHEN_NO_KEY", "true")
os.environ.setdefault("DEEPSEEK_API_KEY", "")

warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated.*",
)

from fastapi.testclient import TestClient

from app.main import app


class MockDialogueTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_mock_dialogue_returns_short_utterances_and_debug_ids(self) -> None:
        cases = [
            ("arknights_amiya", "你知道八重神子吗？", "amiya_boundary_other_worlds"),
            ("genshin_yae_miko", "我想投稿轻小说。", "yae_publishing_house"),
            ("wuwa_jinhsi", "我有一个愿望。", "jinhsi_wish_custom"),
        ]

        for npc_id, player_text, expected_chunk_id in cases:
            with self.subTest(npc_id=npc_id):
                payload = self._payload(npc_id, player_text)
                response = self.client.post("/api/v1/dialogue", json=payload)

                self.assertEqual(response.status_code, 200, response.text)
                body = response.json()
                self.assertEqual(body["schema_version"], "dialogue_response.v1")
                self.assertEqual(body["npc_id"], npc_id)

                utterances = body["utterances"]
                self.assertGreaterEqual(len(utterances), 1)
                self.assertLessEqual(len(utterances), 3)
                for utterance in utterances:
                    self.assertTrue(utterance["text"].strip())
                    self.assertLessEqual(len(utterance["text"]), 28)

                used_knowledge_ids = body["internal"]["used_knowledge_ids"]
                self.assertIn(expected_chunk_id, used_knowledge_ids)

    def test_out_of_range_response_still_matches_response_schema(self) -> None:
        payload = self._payload("arknights_amiya", "你好")
        payload["is_in_range"] = False

        response = self.client.post("/api/v1/dialogue", json=payload)

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["schema_version"], "dialogue_response.v1")
        self.assertEqual(len(body["utterances"]), 1)
        self.assertTrue(body["utterances"][0]["text"])

    @staticmethod
    def _payload(npc_id: str, player_text: str) -> dict:
        return {
            "schema_version": "dialogue_request.v1",
            "session_id": "test_session",
            "player_id": "local_player",
            "npc_id": npc_id,
            "player_text": player_text,
            "distance_m": 2.0,
            "is_in_range": True,
            "world_state": {
                "location_id": "portfolio_whitebox_room",
                "game_time_label": "demo",
                "quest_stage": 0,
                "relationship_score": 0,
                "debug_enabled": True,
            },
        }


if __name__ == "__main__":
    unittest.main()
