from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.models import (
    AgentPlan,
    AgentDialogueResponse,
    AgentTrace,
    InternalDebug,
    NormalizedDialogueResponse,
    ToolCall,
    ToolResult,
    Utterance,
    WorldEvent,
)


class DialogueModelsTest(unittest.TestCase):
    def test_agent_response_serializes_agent_trace_and_world_events(self) -> None:
        response = AgentDialogueResponse(
            turn_id="turn_test_agent",
            npc_id="arknights_amiya",
            utterances=[
                Utterance(
                    text="我明白了，博士。",
                    expression="neutral",
                    action="idle",
                    delay_ms=500,
                )
            ],
            world_events=[
                WorldEvent(
                    event_id="evt_test_quest_started",
                    event_type="quest_started",
                    payload={"quest_id": "shared_field_request", "stage": 1},
                )
            ],
            trace=AgentTrace(
                used_knowledge_ids=["amiya_rhodes_mission"],
                plan=AgentPlan(
                    intent="accept_quest",
                    goal="Start a task after the player agrees to help.",
                    required_knowledge=["amiya_rhodes_mission"],
                    proposed_tools=["start_quest"],
                    public_reason="玩家明确表示愿意帮忙。",
                ),
                tool_calls=[
                    ToolCall(
                        call_id="call_start",
                        tool_name="start_quest",
                        arguments={"quest_id": "shared_field_request"},
                        reason="玩家接受了当前请求。",
                    )
                ],
                tool_results=[
                    ToolResult(
                        call_id="call_start",
                        tool_name="start_quest",
                        ok=True,
                        result={"quest_id": "shared_field_request", "status": "active"},
                    )
                ],
                confidence=0.88,
            ),
        )

        body = response.model_dump()

        self.assertEqual(body["schema_version"], "dialogue_response.agent")
        self.assertEqual(body["world_events"][0]["event_type"], "quest_started")
        self.assertEqual(body["trace"]["plan"]["intent"], "accept_quest")
        self.assertEqual(body["trace"]["tool_results"][0]["ok"], True)

    def test_agent_response_allows_empty_tool_calls(self) -> None:
        response = AgentDialogueResponse(
            turn_id="turn_no_tool",
            npc_id="genshin_yae_miko",
            utterances=[
                Utterance(text="呵，继续说吧。", expression="teasing", action="soft_laugh", delay_ms=500)
            ],
            trace=AgentTrace(
                used_knowledge_ids=["yae_publishing_house"],
                confidence=0.71,
            ),
        )

        body = response.model_dump()

        self.assertEqual(body["trace"]["tool_calls"], [])
        self.assertEqual(body["trace"]["tool_results"], [])
        self.assertEqual(body["world_events"], [])

    def test_normalized_response_model_stays_internal(self) -> None:
        response = NormalizedDialogueResponse(
            turn_id="turn_internal",
            npc_id="wuwa_jinhsi",
            utterances=[Utterance(text="请说。", expression="neutral", action="idle", delay_ms=500)],
            internal=InternalDebug(
                used_knowledge_ids=["jinhsi_wish_custom"],
                used_memory_ids=[],
                confidence=0.9,
            ),
        )

        body = response.model_dump()

        self.assertEqual(body["schema_version"], "dialogue_response.internal")
        self.assertIn("internal", body)
        self.assertNotIn("trace", body)
        self.assertNotIn("world_events", body)

    def test_schema_examples_validate_against_models(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        response_example = json.loads((project_root / "schemas" / "dialogue_response.agent.example.json").read_text(encoding="utf-8"))
        trace_example = json.loads((project_root / "schemas" / "agent_trace.example.json").read_text(encoding="utf-8"))

        response = AgentDialogueResponse.model_validate(response_example)
        trace = AgentTrace.model_validate(trace_example)

        self.assertEqual(response.schema_version, "dialogue_response.agent")
        self.assertEqual(trace.plan.intent, "answer_with_memory")


if __name__ == "__main__":
    unittest.main()
