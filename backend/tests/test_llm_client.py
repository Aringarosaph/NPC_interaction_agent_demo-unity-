from __future__ import annotations

from types import SimpleNamespace
import unittest

from app.llm_client import LlmClient


class FakeCompletions:
    def __init__(self, content: str | None = None, error: Exception | None = None):
        self.content = content
        self.error = error
        self.kwargs = None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        if self.error is not None:
            raise self.error
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.content)
                )
            ]
        )


class FakeClient:
    def __init__(self, completions: FakeCompletions):
        self.chat = SimpleNamespace(completions=completions)


class LlmClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_generate_json_uses_deepseek_json_mode_and_thinking_disabled(self) -> None:
        completions = FakeCompletions(
            content='{"utterances":[{"text":"请说。","emotion":"gentle","action":"nod","delay_ms":500}],"used_knowledge_ids":["k1"],"used_memory_ids":[],"memory_candidates":[],"confidence":0.9}'
        )
        client = LlmClient(
            api_key="test_key",
            base_url="https://example.test",
            model="deepseek-test",
            mock_when_no_key=True,
            client=FakeClient(completions),
        )

        result = await client.generate_json(
            messages=[{"role": "user", "content": "<PLAYER_INPUT>我有一个愿望。</PLAYER_INPUT>"}],
            temperature=0.1,
            max_tokens=120,
        )

        self.assertEqual(result["utterances"][0]["text"], "请说。")
        self.assertEqual(completions.kwargs["model"], "deepseek-test")
        self.assertEqual(completions.kwargs["response_format"], {"type": "json_object"})
        self.assertEqual(completions.kwargs["extra_body"], {"thinking": {"type": "disabled"}})
        self.assertEqual(completions.kwargs["temperature"], 0.1)
        self.assertEqual(completions.kwargs["max_tokens"], 120)

    async def test_generate_json_falls_back_to_mock_when_deepseek_fails(self) -> None:
        completions = FakeCompletions(error=RuntimeError("network failed"))
        client = LlmClient(
            api_key="test_key",
            model="deepseek-test",
            mock_when_no_key=True,
            client=FakeClient(completions),
        )

        result = await client.generate_json(
            messages=[{"role": "user", "content": "<PLAYER_INPUT>我想投稿轻小说。</PLAYER_INPUT>"}],
            temperature=0.1,
            max_tokens=120,
        )

        self.assertEqual(result["utterances"][0]["text"], "听起来有点意思。")
        self.assertEqual(result["confidence"], 0.25)

    async def test_generate_json_falls_back_to_mock_when_json_is_invalid(self) -> None:
        completions = FakeCompletions(content="not json")
        client = LlmClient(
            api_key="test_key",
            model="deepseek-test",
            mock_when_no_key=True,
            client=FakeClient(completions),
        )

        result = await client.generate_json(
            messages=[{"role": "user", "content": "<PLAYER_INPUT>我有一个愿望。</PLAYER_INPUT>"}],
            temperature=0.1,
            max_tokens=120,
        )

        self.assertEqual(result["utterances"][0]["text"], "请说。")
        self.assertEqual(result["confidence"], 0.25)


if __name__ == "__main__":
    unittest.main()
