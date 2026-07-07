from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.state_store import StateStore
from app.tools import ToolExecutionContext, create_default_registry


class StateStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "state.sqlite"
        self.store = StateStore(self.db_path)

    def tearDown(self) -> None:
        self.store.close()
        self.tmpdir.cleanup()

    def test_start_and_advance_quest_persist(self) -> None:
        started = self.store.start_quest("local_player", "arknights_amiya", "shared_field_request")
        advanced = self.store.advance_quest(
            "local_player",
            "arknights_amiya",
            "shared_field_request",
            expected_stage=1,
        )

        self.assertEqual(started["stage"], 1)
        self.assertEqual(started["status"], "active")
        self.assertEqual(advanced["stage"], 2)
        self.assertEqual(advanced["status"], "completed")

        self.store.close()
        reopened = StateStore(self.db_path)
        try:
            persisted = reopened.get_quest_state("local_player", "shared_field_request")
            self.assertEqual(persisted["stage"], 2)
            self.assertEqual(persisted["status"], "completed")
        finally:
            reopened.close()

    def test_relationship_inventory_and_events_are_in_snapshot(self) -> None:
        relationship = self.store.update_relationship(
            player_id="local_player",
            npc_id="genshin_yae_miko",
            delta=7,
            reason="玩家完成了委托。",
        )
        item = self.store.grant_item(
            player_id="local_player",
            item_id="yae_submission_token",
            quantity=2,
            source_turn_id="turn_state_test",
        )
        event = self.store.log_world_event(
            event_type="item_granted",
            npc_id="genshin_yae_miko",
            player_id="local_player",
            payload={"item_id": "yae_submission_token", "quantity": 2},
            source_turn_id="turn_state_test",
        )

        snapshot = self.store.get_player_snapshot("local_player", "genshin_yae_miko")

        self.assertEqual(relationship["relationship_label"], "friendly")
        self.assertEqual(item["quantity"], 2)
        self.assertEqual(event["payload"]["item_id"], "yae_submission_token")
        self.assertEqual(snapshot["relationship"]["relationship_score"], 7)
        self.assertEqual(snapshot["inventory"][0]["item_id"], "yae_submission_token")
        self.assertEqual(snapshot["recent_world_events"][0]["event_type"], "item_granted")

    def test_reset_runtime_clears_player_state(self) -> None:
        self.store.start_quest("local_player", "arknights_amiya", "shared_field_request")
        self.store.update_relationship("local_player", "arknights_amiya", 6, "demo")
        self.store.grant_item("local_player", "demo_badge", 1, "turn_reset")
        self.store.log_world_event("demo_event", "arknights_amiya", "local_player", {"ok": True})

        counts = self.store.reset_runtime(player_id="local_player")
        quest = self.store.get_quest_state("local_player", "shared_field_request")
        snapshot = self.store.get_player_snapshot("local_player", "arknights_amiya")

        self.assertEqual(counts["quest_states"], 1)
        self.assertEqual(counts["npc_relationships"], 1)
        self.assertEqual(counts["inventory_items"], 1)
        self.assertEqual(counts["world_events"], 1)
        self.assertEqual(quest["status"], "not_started")
        self.assertEqual(snapshot["relationship"]["relationship_label"], "neutral")
        self.assertEqual(snapshot["inventory"], [])

    def test_advance_requires_active_quest_and_expected_stage(self) -> None:
        with self.assertRaises(ValueError):
            self.store.advance_quest("local_player", "wuwa_jinhsi", "shared_field_request")

        self.store.start_quest("local_player", "wuwa_jinhsi", "shared_field_request")

        with self.assertRaises(ValueError):
            self.store.advance_quest(
                "local_player",
                "wuwa_jinhsi",
                "shared_field_request",
                expected_stage=9,
            )

    def test_default_tool_registry_uses_state_store_backend(self) -> None:
        registry = create_default_registry(self.store)
        context = ToolExecutionContext(
            npc_id="wuwa_jinhsi",
            player_id="local_player",
            session_id="state_store_tool_test",
            turn_id="turn_tool_state",
        )

        start = registry.execute("start_quest", {"quest_id": "shared_field_request"}, context)
        relationship = registry.execute("update_relationship", {"delta": 6, "reason": "完成请求"}, context)

        self.assertTrue(start.ok, start.error)
        self.assertTrue(relationship.ok, relationship.error)
        self.assertEqual(start.result["world_event"]["event_type"], "quest_started")
        self.assertEqual(relationship.result["relationship_label"], "friendly")

        snapshot = self.store.get_player_snapshot("local_player", "wuwa_jinhsi")
        self.assertEqual(snapshot["quests"][0]["status"], "active")
        self.assertEqual(len(snapshot["recent_world_events"]), 2)


if __name__ == "__main__":
    unittest.main()
