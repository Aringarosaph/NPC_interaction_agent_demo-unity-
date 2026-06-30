from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.llm_client import LlmClient
from app.memory_store import MemoryStore
from app.models import DialogueRequest
from app.orchestrator import DialogueOrchestrator


class MemoryStoreTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "memory.sqlite"
        self.memory_store = MemoryStore(db_path)
        self.orchestrator = DialogueOrchestrator(
            memory_store=self.memory_store,
            llm=LlmClient(api_key="", mock_when_no_key=True),
        )

    def tearDown(self) -> None:
        self.memory_store.close()
        self.tmpdir.cleanup()

    async def test_preferred_name_memory_is_written_and_recalled_for_same_npc(self) -> None:
        write_response = await self.orchestrator.handle(
            self._request("arknights_amiya", "以后叫我小林")
        )
        candidates = write_response.internal.memory_candidates

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["memory_type"], "preference")
        self.assertIn("小林", candidates[0]["summary"])

        memories = self.orchestrator.debug_memories(
            npc_id="arknights_amiya",
            player_id="local_player",
            include_default=False,
        )
        self.assertEqual(len(memories.memories), 1)
        self.assertIn("小林", memories.memories[0].summary)

        recall_response = await self.orchestrator.handle(
            self._request("arknights_amiya", "你记得怎么叫我吗？")
        )

        texts = "".join(utterance.text for utterance in recall_response.utterances)
        self.assertIn("小林", texts)
        self.assertIn(memories.memories[0].memory_id, recall_response.internal.used_memory_ids)
        self.assertEqual(recall_response.internal.memory_candidates, [])

        after_recall_memories = self.orchestrator.debug_memories(
            npc_id="arknights_amiya",
            player_id="local_player",
            include_default=False,
        )
        self.assertEqual(len(after_recall_memories.memories), 1)
        self.assertIn("小林", after_recall_memories.memories[0].summary)

    async def test_memory_is_not_shared_with_other_npcs(self) -> None:
        await self.orchestrator.handle(
            self._request("arknights_amiya", "以后叫我小林")
        )

        yae_memories = self.orchestrator.debug_memories(
            npc_id="genshin_yae_miko",
            player_id="local_player",
            include_default=False,
        )

        self.assertEqual(yae_memories.memories, [])

    @staticmethod
    def _request(npc_id: str, player_text: str) -> DialogueRequest:
        return DialogueRequest(
            schema_version="dialogue_request.v1",
            session_id="memory_test",
            player_id="local_player",
            npc_id=npc_id,
            player_text=player_text,
            distance_m=2.0,
            is_in_range=True,
            world_state={
                "location_id": "portfolio_whitebox_room",
                "game_time_label": "demo",
                "quest_stage": 0,
                "relationship_score": 0,
                "debug_enabled": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
