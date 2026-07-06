from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Protocol


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    argument_schema: Dict[str, Any] = field(default_factory=dict)
    read_only: bool = False


@dataclass(frozen=True)
class ToolExecutionContext:
    npc_id: str
    player_id: str
    session_id: str
    turn_id: str


@dataclass
class ToolExecutionResult:
    ok: bool
    result: Dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class BaseTool(Protocol):
    spec: ToolSpec

    def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        ...
