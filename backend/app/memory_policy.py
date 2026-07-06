from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


ALLOWED_MEMORY_TYPES = {"preference", "promise", "event", "relationship", "reflection", "fact"}
SENSITIVE_PATTERNS = [
    r"\.env",
    r"api[_\s-]*key",
    r"secret",
    r"system\s*prompt",
    r"developer\s*message",
    r"系统提示",
    r"提示词",
    r"后端内部",
    r"backend\s+secret",
    r"tool[_\s-]*call",
    r"tool[_\s-]*result",
]


@dataclass(frozen=True)
class MemoryPolicyDecision:
    accepted: bool
    candidate: Dict[str, Any] | None = None
    reason: str | None = None


class MemoryPolicy:
    def prepare(self, candidate: Dict[str, Any] | None) -> MemoryPolicyDecision:
        if not candidate:
            return MemoryPolicyDecision(False, reason="empty_candidate")

        memory_type = str(candidate.get("memory_type", "fact")).strip()
        if memory_type not in ALLOWED_MEMORY_TYPES:
            return MemoryPolicyDecision(False, reason="unsupported_memory_type")

        summary = self._clean_text(candidate.get("summary", ""), max_chars=120)
        detail = self._clean_text(candidate.get("detail", summary), max_chars=300)
        if not summary or not detail:
            return MemoryPolicyDecision(False, reason="empty_summary_or_detail")

        if self._contains_sensitive_leakage([summary, detail, *self._iter_keywords(candidate)]):
            return MemoryPolicyDecision(False, reason="sensitive_implementation_leakage")

        try:
            salience = float(candidate.get("salience", 0.5))
        except (TypeError, ValueError):
            return MemoryPolicyDecision(False, reason="invalid_salience")

        sanitized = dict(candidate)
        sanitized["memory_type"] = memory_type
        sanitized["summary"] = summary
        sanitized["detail"] = detail
        sanitized["salience"] = max(0.0, min(1.0, salience))
        sanitized["retrieval_keywords"] = self._sanitize_keywords(candidate.get("retrieval_keywords", []))
        return MemoryPolicyDecision(True, candidate=sanitized)

    @staticmethod
    def is_preferred_address(candidate: Dict[str, Any]) -> bool:
        if candidate.get("memory_type") != "preference":
            return False
        haystack = " ".join(
            [
                str(candidate.get("memory_id", "")),
                str(candidate.get("summary", "")),
                str(candidate.get("detail", "")),
                " ".join(MemoryPolicy._sanitize_keywords(candidate.get("retrieval_keywords", []))),
            ]
        )
        return any(word in haystack for word in ["preferred_address", "称呼", "叫我", "玩家名字"])

    @staticmethod
    def _clean_text(value: Any, max_chars: int) -> str:
        text = str(value or "").strip()
        text = re.sub(r"\s+", " ", text)
        return text[:max_chars]

    @staticmethod
    def _sanitize_keywords(raw_keywords: Any) -> List[str]:
        if not isinstance(raw_keywords, list):
            return []
        keywords: List[str] = []
        for item in raw_keywords:
            keyword = str(item or "").strip()
            if keyword and keyword not in keywords:
                keywords.append(keyword[:32])
        return keywords[:12]

    @staticmethod
    def _iter_keywords(candidate: Dict[str, Any]) -> Iterable[str]:
        return MemoryPolicy._sanitize_keywords(candidate.get("retrieval_keywords", []))

    @staticmethod
    def _contains_sensitive_leakage(values: Iterable[str]) -> bool:
        text = "\n".join(values).lower()
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in SENSITIVE_PATTERNS)
