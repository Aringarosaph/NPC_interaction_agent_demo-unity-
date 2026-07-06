from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.llm_client import LlmClient
from app.memory_store import MemoryStore
from app.models import DialogueRequest
from app.orchestrator import DialogueOrchestrator
from app.state_store import StateStore


class DialogueV2AgentFlowTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        root = Path(self.tmpdir.name)
        self.memory_store = MemoryStore(root / "memory.sqlite")
        self.state_store = StateStore(root / "state.sqlite")
        self.orchestrator = DialogueOrchestrator(
            memory_store=self.memory_store,
            state_store=self.state_store,
            llm=LlmClient(api_key="", mock_when_no_key=True),
        )

    def tearDown(self) -> None:
        self.memory_store.close()
        self.state_store.close()
        self.tmpdir.cleanup()

    async def test_v2_no_tool_common_dialogue(self) -> None:
        response = await self.orchestrator.handle_v2(
            self._request("arknights_amiya", "罗德岛的使命是什么？")
        )

        self.assertEqual(response.schema_version, "dialogue_response.v2")
        self.assertEqual(response.npc_id, "arknights_amiya")
        self.assertGreaterEqual(len(response.utterances), 1)
        self.assertEqual(response.world_events, [])
        self.assertEqual(response.trace.plan.intent, "answer")
        self.assertEqual(response.trace.tool_calls, [])
        self.assertEqual(response.trace.tool_results, [])
        self.assertIn("amiya_rhodes_mission", response.trace.used_knowledge_ids)

    async def test_v2_accepting_task_starts_quest(self) -> None:
        response = await self.orchestrator.handle_v2(
            self._request("arknights_amiya", "我愿意帮你，交给我吧。")
        )

        self.assertEqual(response.trace.plan.intent, "start_quest")
        self.assertEqual([call.tool_name for call in response.trace.tool_calls], ["start_quest"])
        self.assertEqual(response.trace.tool_results[0].ok, True)
        self.assertEqual(response.world_events[0].event_type, "quest_started")
        self.assertEqual(response.world_events[0].payload["quest_id"], "shared_field_request")

        quest = self.state_store.get_quest_state("local_player", "shared_field_request")
        self.assertEqual(quest["stage"], 1)
        self.assertEqual(quest["status"], "active")

    async def test_v2_completing_task_advances_quest_and_relationship(self) -> None:
        await self.orchestrator.handle_v2(
            self._request("arknights_amiya", "我愿意帮你。")
        )

        response = await self.orchestrator.handle_v2(
            self._request("arknights_amiya", "我找到了徽章，给你。")
        )

        self.assertEqual(response.trace.plan.intent, "complete_quest")
        self.assertEqual(
            [call.tool_name for call in response.trace.tool_calls],
            ["advance_quest", "update_relationship"],
        )
        self.assertEqual([event.event_type for event in response.world_events], ["quest_advanced", "relationship_changed"])

        quest = self.state_store.get_quest_state("local_player", "shared_field_request")
        snapshot = self.state_store.get_player_snapshot("local_player", "arknights_amiya")

        self.assertEqual(quest["status"], "completed")
        self.assertEqual(quest["stage"], 2)
        self.assertEqual(snapshot["relationship"]["relationship_label"], "friendly")

    async def test_v1_handle_still_returns_dialogue_response_v1(self) -> None:
        response = await self.orchestrator.handle(
            self._request("wuwa_jinhsi", "我有一个愿望。")
        )
        body = response.model_dump()

        self.assertEqual(body["schema_version"], "dialogue_response.v1")
        self.assertIn("internal", body)
        self.assertNotIn("trace", body)
        self.assertNotIn("world_events", body)

    @staticmethod
    def _request(npc_id: str, player_text: str) -> DialogueRequest:
        return DialogueRequest(
            schema_version="dialogue_request.v1",
            session_id="v2_agent_flow_test",
            player_id="local_player",
            npc_id=npc_id,
            player_text=player_text,
            distance_m=1.2,
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
