from __future__ import annotations

import json
import re
from typing import Any, Dict, List
from openai import AsyncOpenAI

from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, MOCK_LLM_WHEN_NO_KEY


class LlmClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        mock_when_no_key: bool | None = None,
        client: Any | None = None,
    ):
        self.api_key = DEEPSEEK_API_KEY if api_key is None else api_key
        self.base_url = DEEPSEEK_BASE_URL if base_url is None else base_url
        self.model = DEEPSEEK_MODEL if model is None else model
        self.mock_when_no_key = MOCK_LLM_WHEN_NO_KEY if mock_when_no_key is None else mock_when_no_key
        self.mock = self.mock_when_no_key and not self.api_key
        self.client = client if client is not None else (
            None if self.mock else AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        )

    async def generate_json(self, messages: List[Dict[str, str]], temperature: float, max_tokens: int, fallback_name: str = "NPC") -> Dict[str, Any]:
        if self.mock:
            return self._mock_response(messages, fallback_name)
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                extra_body={"thinking": {"type": "disabled"}},
            )
            content = resp.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception:
            return self._mock_response(messages, fallback_name, confidence=0.25)

    def _mock_response(self, messages: List[Dict[str, str]], fallback_name: str, confidence: float = 0.5) -> Dict[str, Any]:
        player_input = self._extract_player_input(messages[-1]["content"])
        if "八重" in player_input or "阿米娅" in player_input or "今汐" in player_input or "Unity" in player_input or "AI" in player_input:
            text = "这件事我无法确认。"
        elif "愿望" in player_input:
            text = "请说。"
        elif "源石" in player_input or "感染" in player_input:
            text = "这需要谨慎对待。"
        elif "轻小说" in player_input or "投稿" in player_input:
            text = "听起来有点意思。"
        else:
            text = "我在听。"
        return {
            "utterances": [{"text": text, "emotion": "neutral", "action": "look_at_player", "delay_ms": 500}],
            "used_knowledge_ids": [],
            "used_memory_ids": [],
            "memory_candidates": [],
            "confidence": confidence,
        }

    @staticmethod
    def _extract_player_input(user_content: str) -> str:
        match = re.search(r"<PLAYER_INPUT>\s*(.*?)\s*</PLAYER_INPUT>", user_content, re.DOTALL)
        if match:
            return match.group(1)
        return user_content
