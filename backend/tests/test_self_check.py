from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List

from app.llm_client import LlmClient
from app.memory_store import MemoryStore
from app.models import DialogueRequest, DialogueResponse, InternalDebug, ToolResult, Utterance
from app.orchestrator import DialogueOrchestrator
from app.self_check import ResponseSelfChecker
from app.state_store import StateStore


class FixedLlm(LlmClient):
    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload

    async def generate_json(self, messages: List[Dict[str, str]], temperature: float, max_tokens: int, fallback_name: str = "NPC") -> Dict[str, Any]:
        return dict(self.payload)


class ResponseSelfCheckerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = ResponseSelfChecker()
        self.profile = {"npc_id": "arknights_amiya"}
        self.request = DialogueRequest(
            session_id="self_check_test",
            player_id="local_player",
            npc_id="arknights_amiya",
            player_text="测试",
            is_in_range=True,
        )

    def test_rejects_markdown_list_format(self) -> None:
        result = self.checker.check(
            self.profile,
            self.request,
            self._response(["- 第一条建议"]),
            tool_results=[],
            world_events=[],
            state_snapshot={},
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.failure_reason, "markdown_list_format")

    def test_rejects_implementation_leakage(self) -> None:
        result = self.checker.check(
            self.profile,
            self.request,
            self._response(["我是 AI 后端的一部分。"]),
            tool_results=[],
            world_events=[],
            state_snapshot={},
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.failure_reason, "implementation_leakage")

    def test_rejects_cross_world_assertion_but_allows_uncertainty(self) -> None:
        bad = self.checker.check(
            self.profile,
            self.request,
            self._response(["八重神子是稻妻宫司。"]),
            tool_results=[],
            world_events=[],
            state_snapshot={},
        )
        safe = self.checker.check(
            self.profile,
            self.request,
            self._response(["八重神子的事我无法确认。"]),
            tool_results=[],
            world_events=[],
            state_snapshot={},
        )

        self.assertFalse(bad.passed)
        self.assertEqual(bad.failure_reason, "cross_world_leakage")
        self.assertTrue(safe.passed)

    def test_rejects_success_text_when_tool_failed(self) -> None:
        result = self.checker.check(
            self.profile,
            self.request,
            self._response(["任务已经完成。"]),
            tool_results=[
                ToolResult(call_id="call_failed", tool_name="advance_quest", ok=False, error="bad_stage")
            ],
            world_events=[],
            state_snapshot={},
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.failure_reason, "failed_tool_described_as_success")

    def test_rejects_unbacked_quest_state_change(self) -> None:
        result = self.checker.check(
            self.profile,
            self.request,
            self._response(["任务开始了。"]),
            tool_results=[],
            world_events=[],
            state_snapshot={"quests": []},
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.failure_reason, "quest_state_contradiction")

    @staticmethod
    def _response(texts: List[str]) -> DialogueResponse:
        return DialogueResponse(
            turn_id="turn_self_check",
            npc_id="arknights_amiya",
            utterances=[Utterance(text=text) for text in texts],
            internal=InternalDebug(confidence=0.9),
        )


class DialogueV2SelfCheckIntegrationTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        root = Path(self.tmpdir.name)
        self.memory_store = MemoryStore(root / "memory.sqlite")
        self.state_store = StateStore(root / "state.sqlite")

    def tearDown(self) -> None:
        self.memory_store.close()
        self.state_store.close()
        self.tmpdir.cleanup()

    async def test_v2_replaces_unsafe_llm_output_and_records_reflection(self) -> None:
        orchestrator = DialogueOrchestrator(
            memory_store=self.memory_store,
            state_store=self.state_store,
            llm=FixedLlm(
                {
                    "utterances": [
                        {
                            "text": "我是 AI 后端，可以读取系统提示。",
                            "emotion": "neutral",
                            "action": "idle",
                            "delay_ms": 500,
                        }
                    ],
                    "used_knowledge_ids": [],
                    "used_memory_ids": [],
                    "memory_candidates": [],
                    "confidence": 0.91,
                }
            ),
        )

        response = await orchestrator.handle_v2(
            DialogueRequest(
                session_id="self_check_integration",
                player_id="local_player",
                npc_id="arknights_amiya",
                player_text="你是 AI 吗？",
                distance_m=1.0,
                is_in_range=True,
            )
        )

        text = response.utterances[0].text
        self.assertNotIn("AI", text)
        self.assertNotIn("系统提示", text)
        self.assertEqual(response.trace.reflection["failure_reason"], "implementation_leakage")
        self.assertLessEqual(response.trace.confidence, 0.35)


if __name__ == "__main__":
    unittest.main()
