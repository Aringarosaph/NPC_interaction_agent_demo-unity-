from __future__ import annotations

import unittest

from app.tools import InMemoryGameState, ToolExecutionContext, ToolRegistry, create_default_registry


class ToolRegistryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.state = InMemoryGameState()
        self.registry = create_default_registry(self.state)
        self.context = ToolExecutionContext(
            npc_id="arknights_amiya",
            player_id="local_player",
            session_id="test_session",
            turn_id="turn_tool_test",
        )

    def test_unregistered_tool_fails(self) -> None:
        registry = ToolRegistry()

        result = registry.execute("missing_tool", {}, self.context)

        self.assertFalse(result.ok)
        self.assertIn("unregistered tool", result.error or "")

    def test_missing_required_argument_fails(self) -> None:
        result = self.registry.execute("start_quest", {}, self.context)

        self.assertFalse(result.ok)
        self.assertIn("missing required argument: quest_id", result.error or "")
        self.assertEqual(self.state.quest_states, {})

    def test_invalid_argument_type_fails_before_execution(self) -> None:
        result = self.registry.execute("grant_item", {"item_id": "supply_note", "quantity": "one"}, self.context)

        self.assertFalse(result.ok)
        self.assertIn("invalid argument type", result.error or "")
        self.assertEqual(self.state.inventory, {})

    def test_read_only_tool_does_not_modify_quest_or_events(self) -> None:
        result = self.registry.execute("get_quest_state", {"quest_id": "shared_field_request"}, self.context)

        self.assertTrue(result.ok)
        self.assertEqual(result.result["status"], "not_started")
        self.assertEqual(self.state.quest_states, {})
        self.assertEqual(self.state.world_events, [])

    def test_start_and_advance_quest_return_structured_results(self) -> None:
        start = self.registry.execute("start_quest", {"quest_id": "shared_field_request"}, self.context)
        advance = self.registry.execute(
            "advance_quest",
            {"quest_id": "shared_field_request", "expected_stage": 1},
            self.context,
        )

        self.assertTrue(start.ok, start.error)
        self.assertEqual(start.result["status"], "active")
        self.assertEqual(start.result["stage"], 1)
        self.assertEqual(start.result["world_event"]["event_type"], "quest_started")

        self.assertTrue(advance.ok, advance.error)
        self.assertEqual(advance.result["status"], "completed")
        self.assertEqual(advance.result["stage"], 2)
        self.assertEqual(advance.result["world_event"]["event_type"], "quest_advanced")
        self.assertEqual(len(self.state.world_events), 2)

    def test_update_relationship_and_grant_item_emit_events(self) -> None:
        relationship = self.registry.execute(
            "update_relationship",
            {"delta": 8, "reason": "玩家完成了请求。"},
            self.context,
        )
        item = self.registry.execute(
            "grant_item",
            {"item_id": "amiya_field_note", "quantity": 1},
            self.context,
        )

        self.assertTrue(relationship.ok, relationship.error)
        self.assertEqual(relationship.result["relationship_label"], "friendly")
        self.assertEqual(relationship.result["world_event"]["event_type"], "relationship_changed")

        self.assertTrue(item.ok, item.error)
        self.assertEqual(item.result["quantity"], 1)
        self.assertEqual(item.result["world_event"]["event_type"], "item_granted")

    def test_registry_lists_tool_specs(self) -> None:
        specs = self.registry.list_specs()

        names = {spec.name for spec in specs}
        self.assertIn("get_player_state", names)
        self.assertIn("start_quest", names)
        self.assertIn("advance_quest", names)
        self.assertIn("emit_world_event", names)


if __name__ == "__main__":
    unittest.main()
