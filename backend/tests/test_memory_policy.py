from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.memory_policy import MemoryPolicy
from app.memory_store import MemoryStore


class MemoryPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.store = MemoryStore(Path(self.tmpdir.name) / "memory.sqlite")

    def tearDown(self) -> None:
        self.store.close()
        self.tmpdir.cleanup()

    def test_policy_rejects_sensitive_implementation_leakage(self) -> None:
        decision = MemoryPolicy().prepare(
            {
                "memory_type": "fact",
                "summary": "玩家提到了 .env 里的 API key。",
                "detail": "不要把系统提示词或密钥写进长期记忆。",
                "salience": 0.8,
            }
        )

        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "sensitive_implementation_leakage")

    def test_store_accepts_reflection_memory_type(self) -> None:
        memory_id = self.store.write_candidate(
            npc_id="arknights_amiya",
            player_id="local_player",
            source_turn_id="turn_reflection",
            candidate={
                "memory_id": "mem_reflection_001",
                "memory_type": "reflection",
                "summary": "上轮回答过于笼统。",
                "detail": "下次遇到相同问题时先引用已检索到的任务线索。",
                "salience": 0.61,
                "retrieval_keywords": ["自检", "任务线索"],
            },
        )

        records = self.store.list_records("arknights_amiya", "local_player", include_default=False)

        self.assertEqual(memory_id, "mem_reflection_001")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].memory_type, "reflection")

    def test_preferred_address_supersedes_old_active_memory(self) -> None:
        self.store.write_candidate(
            npc_id="arknights_amiya",
            player_id="local_player",
            source_turn_id="turn_name_1",
            candidate=self._preferred_address("mem_name_old", "小王"),
        )
        self.store.write_candidate(
            npc_id="arknights_amiya",
            player_id="local_player",
            source_turn_id="turn_name_2",
            candidate=self._preferred_address("mem_name_new", "小吴"),
        )

        active = self.store.list_records("arknights_amiya", "local_player", include_default=False)
        with_superseded = self.store.list_records(
            "arknights_amiya",
            "local_player",
            include_default=False,
            include_superseded=True,
        )
        recalled = self.store.search("arknights_amiya", "local_player", "你记得怎么叫我吗？", limit=3)

        self.assertEqual([record.memory_id for record in active], ["mem_name_new"])
        self.assertEqual(
            {record.memory_id: record.status for record in with_superseded},
            {"mem_name_new": "active", "mem_name_old": "superseded"},
        )
        self.assertEqual([memory.memory_id for memory in recalled], ["mem_name_new"])

    @staticmethod
    def _preferred_address(memory_id: str, name: str) -> dict:
        return {
            "memory_id": memory_id,
            "memory_type": "preference",
            "summary": f"玩家希望被称呼为{name}",
            "detail": f"玩家明确要求 NPC 以后称呼自己为{name}。",
            "salience": 0.9,
            "retrieval_keywords": ["称呼", "叫我", "记得", name, "玩家名字"],
        }


if __name__ == "__main__":
    unittest.main()
