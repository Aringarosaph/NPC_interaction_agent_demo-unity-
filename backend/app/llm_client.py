from __future__ import annotations

import json
import re
from typing import Any, Dict, List
from openai import AsyncOpenAI

from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, MOCK_LLM_WHEN_NO_KEY


class LlmClient:
    def __init__(self):
        self.mock = MOCK_LLM_WHEN_NO_KEY and not DEEPSEEK_API_KEY
        self.client = None if self.mock else AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

    async def generate_json(self, messages: List[Dict[str, str]], temperature: float, max_tokens: int, fallback_name: str = "NPC") -> Dict[str, Any]:
        if self.mock:
            return self._mock_response(messages, fallback_name)
        try:
            resp = await self.client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                extra_body={"thinking": {"type": "disabled"}},
            )
            content = resp.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception:
            return self._mock_response(messages, fallback_name)

    def _mock_response(self, messages: List[Dict[str, str]], fallback_name: str) -> Dict[str, Any]:
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
            "confidence": 0.5,
        }

    @staticmethod
    def _extract_player_input(user_content: str) -> str:
        match = re.search(r"<PLAYER_INPUT>\s*(.*?)\s*</PLAYER_INPUT>", user_content, re.DOTALL)
        if match:
            return match.group(1)
        return user_content
