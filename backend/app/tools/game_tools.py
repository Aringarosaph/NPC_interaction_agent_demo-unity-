from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Protocol, Tuple

from ..state_store import StateStore
from .base import ToolExecutionContext, ToolExecutionResult, ToolSpec
from .registry import ToolRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _relationship_label(score: float) -> str:
    if score >= 20:
        return "trusted"
    if score >= 5:
        return "friendly"
    if score <= -10:
        return "strained"
    return "neutral"


class GameStateBackend(Protocol):
    def get_player_snapshot(self, player_id: str, npc_id: str) -> Dict[str, Any]:
        ...

    def get_quest_state(self, player_id: str, quest_id: str) -> Dict[str, Any]:
        ...

    def start_quest(self, player_id: str, npc_id: str, quest_id: str) -> Dict[str, Any]:
        ...

    def advance_quest(self, player_id: str, npc_id: str, quest_id: str, expected_stage: int | None = None) -> Dict[str, Any]:
        ...

    def update_relationship(self, player_id: str, npc_id: str, delta: float, reason: str = "") -> Dict[str, Any]:
        ...

    def grant_item(self, player_id: str, item_id: str, quantity: int, source_turn_id: str) -> Dict[str, Any]:
        ...

    def log_world_event(
        self,
        event_type: str,
        npc_id: str,
        player_id: str,
        payload: Dict[str, Any],
        player_visible: bool = True,
        source_turn_id: str | None = None,
        event_id: str | None = None,
    ) -> Dict[str, Any]:
        ...


@dataclass
class InMemoryGameState:
    player_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    quest_states: Dict[Tuple[str, str], Dict[str, Any]] = field(default_factory=dict)
    relationships: Dict[Tuple[str, str], Dict[str, Any]] = field(default_factory=dict)
    inventory: Dict[Tuple[str, str], Dict[str, Any]] = field(default_factory=dict)
    world_events: list[Dict[str, Any]] = field(default_factory=list)

    def get_player_snapshot(self, player_id: str, npc_id: str) -> Dict[str, Any]:
        return {
            "player": self._ensure_player(player_id),
            "relationship": self.relationships.get(
                (npc_id, player_id),
                {
                    "npc_id": npc_id,
                    "player_id": player_id,
                    "relationship_score": 0.0,
                    "relationship_label": "neutral",
                    "updated_at": None,
                },
            ),
            "quests": [dict(record) for (owner, _), record in self.quest_states.items() if owner == player_id],
            "inventory": [dict(record) for (owner, _), record in self.inventory.items() if owner == player_id],
            "recent_world_events": [dict(event) for event in self.world_events if event["player_id"] == player_id][-10:],
        }

    def get_quest_state(self, player_id: str, quest_id: str) -> Dict[str, Any]:
        record = self.quest_states.get((player_id, quest_id))
        if record is None:
            return {
                "quest_id": quest_id,
                "player_id": player_id,
                "npc_id": "",
                "stage": 0,
                "status": "not_started",
                "updated_at": None,
            }
        return dict(record)

    def start_quest(self, player_id: str, npc_id: str, quest_id: str) -> Dict[str, Any]:
        self._ensure_player(player_id)
        key = (player_id, quest_id)
        record = self.quest_states.get(key)
        if record is None:
            record = {
                "quest_id": quest_id,
                "player_id": player_id,
                "npc_id": npc_id,
                "stage": 1,
                "status": "active",
                "updated_at": _now(),
            }
            self.quest_states[key] = record
        elif record.get("status") == "not_started":
            record.update({"npc_id": npc_id, "stage": 1, "status": "active", "updated_at": _now()})
        return dict(record)

    def advance_quest(self, player_id: str, npc_id: str, quest_id: str, expected_stage: int | None = None) -> Dict[str, Any]:
        self._ensure_player(player_id)
        key = (player_id, quest_id)
        record = self.quest_states.get(key)
        if record is None or record.get("status") == "not_started":
            raise ValueError(f"quest is not active: {quest_id}")
        if expected_stage is not None and record.get("stage") != expected_stage:
            raise ValueError(f"quest stage mismatch: expected {expected_stage}, got {record.get('stage')}")
        record["npc_id"] = npc_id
        record["stage"] = int(record.get("stage", 0)) + 1
        record["status"] = "completed" if record["stage"] >= 2 else "active"
        record["updated_at"] = _now()
        return dict(record)

    def update_relationship(self, player_id: str, npc_id: str, delta: float, reason: str = "") -> Dict[str, Any]:
        self._ensure_player(player_id)
        key = (npc_id, player_id)
        record = self.relationships.setdefault(
            key,
            {
                "npc_id": npc_id,
                "player_id": player_id,
                "relationship_score": 0.0,
                "relationship_label": "neutral",
                "updated_at": None,
            },
        )
        record["relationship_score"] = float(record["relationship_score"]) + float(delta)
        record["relationship_label"] = _relationship_label(record["relationship_score"])
        record["updated_at"] = _now()
        record["delta"] = float(delta)
        record["reason"] = reason
        return dict(record)

    def grant_item(self, player_id: str, item_id: str, quantity: int, source_turn_id: str) -> Dict[str, Any]:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self._ensure_player(player_id)
        key = (player_id, item_id)
        record = self.inventory.setdefault(
            key,
            {
                "player_id": player_id,
                "item_id": item_id,
                "quantity": 0,
                "source_turn_id": source_turn_id,
                "updated_at": _now(),
            },
        )
        record["quantity"] = int(record["quantity"]) + int(quantity)
        record["source_turn_id"] = source_turn_id
        record["updated_at"] = _now()
        return dict(record)

    def log_world_event(
        self,
        event_type: str,
        npc_id: str,
        player_id: str,
        payload: Dict[str, Any],
        player_visible: bool = True,
        source_turn_id: str | None = None,
        event_id: str | None = None,
    ) -> Dict[str, Any]:
        event = {
            "event_id": event_id or f"evt_{uuid.uuid4().hex[:12]}",
            "event_type": event_type,
            "npc_id": npc_id,
            "player_id": player_id,
            "payload": payload,
            "player_visible": player_visible,
            "created_at": _now(),
            "source_turn_id": source_turn_id,
        }
        self.world_events.append(event)
        return dict(event)

    def _ensure_player(self, player_id: str) -> Dict[str, Any]:
        return self.player_states.setdefault(
            player_id,
            {
                "player_id": player_id,
                "current_location_id": "portfolio_whitebox_room",
                "created_at": _now(),
                "updated_at": _now(),
            },
        )


class GetPlayerStateTool:
    spec = ToolSpec(
        name="get_player_state",
        description="Read the current player, relationship, quest, inventory, and recent event snapshot.",
        argument_schema={"type": "object", "properties": {}, "required": []},
        read_only=True,
    )

    def __init__(self, state: GameStateBackend):
        self.state = state

    def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        return ToolExecutionResult(
            ok=True,
            result=self.state.get_player_snapshot(context.player_id, context.npc_id),
        )


class GetQuestStateTool:
    spec = ToolSpec(
        name="get_quest_state",
        description="Read quest state for the current player.",
        argument_schema={
            "type": "object",
            "properties": {"quest_id": {"type": "string"}},
            "required": ["quest_id"],
        },
        read_only=True,
    )

    def __init__(self, state: GameStateBackend):
        self.state = state

    def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        return ToolExecutionResult(
            ok=True,
            result=self.state.get_quest_state(context.player_id, arguments["quest_id"]),
        )


class StartQuestTool:
    spec = ToolSpec(
        name="start_quest",
        description="Start a quest for the current player.",
        argument_schema={
            "type": "object",
            "properties": {"quest_id": {"type": "string"}},
            "required": ["quest_id"],
        },
        read_only=False,
    )

    def __init__(self, state: GameStateBackend):
        self.state = state

    def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        quest = self.state.start_quest(context.player_id, context.npc_id, arguments["quest_id"])
        event = self.state.log_world_event(
            event_type="quest_started",
            npc_id=context.npc_id,
            player_id=context.player_id,
            payload={"quest_id": quest["quest_id"], "stage": quest["stage"], "status": quest["status"]},
            source_turn_id=context.turn_id,
        )
        return ToolExecutionResult(ok=True, result={**quest, "world_event": event})


class AdvanceQuestTool:
    spec = ToolSpec(
        name="advance_quest",
        description="Advance an active quest for the current player.",
        argument_schema={
            "type": "object",
            "properties": {
                "quest_id": {"type": "string"},
                "expected_stage": {"type": "integer"},
            },
            "required": ["quest_id"],
        },
        read_only=False,
    )

    def __init__(self, state: GameStateBackend):
        self.state = state

    def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        quest = self.state.advance_quest(
            context.player_id,
            context.npc_id,
            arguments["quest_id"],
            expected_stage=arguments.get("expected_stage"),
        )
        event = self.state.log_world_event(
            event_type="quest_advanced",
            npc_id=context.npc_id,
            player_id=context.player_id,
            payload={"quest_id": quest["quest_id"], "stage": quest["stage"], "status": quest["status"]},
            source_turn_id=context.turn_id,
        )
        return ToolExecutionResult(ok=True, result={**quest, "world_event": event})


class UpdateRelationshipTool:
    spec = ToolSpec(
        name="update_relationship",
        description="Adjust relationship score between the current NPC and player.",
        argument_schema={
            "type": "object",
            "properties": {
                "delta": {"type": "number"},
                "reason": {"type": "string"},
            },
            "required": ["delta"],
        },
        read_only=False,
    )

    def __init__(self, state: GameStateBackend):
        self.state = state

    def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        relationship = self.state.update_relationship(
            player_id=context.player_id,
            npc_id=context.npc_id,
            delta=float(arguments["delta"]),
            reason=arguments.get("reason", ""),
        )
        event = self.state.log_world_event(
            event_type="relationship_changed",
            npc_id=context.npc_id,
            player_id=context.player_id,
            payload={
                "relationship_score": relationship["relationship_score"],
                "relationship_label": relationship["relationship_label"],
                "delta": float(arguments["delta"]),
            },
            source_turn_id=context.turn_id,
        )
        return ToolExecutionResult(ok=True, result={**relationship, "world_event": event})


class GrantItemTool:
    spec = ToolSpec(
        name="grant_item",
        description="Grant an inventory item to the current player.",
        argument_schema={
            "type": "object",
            "properties": {
                "item_id": {"type": "string"},
                "quantity": {"type": "integer"},
            },
            "required": ["item_id", "quantity"],
        },
        read_only=False,
    )

    def __init__(self, state: GameStateBackend):
        self.state = state

    def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        item = self.state.grant_item(
            player_id=context.player_id,
            item_id=arguments["item_id"],
            quantity=int(arguments["quantity"]),
            source_turn_id=context.turn_id,
        )
        event = self.state.log_world_event(
            event_type="item_granted",
            npc_id=context.npc_id,
            player_id=context.player_id,
            payload={"item_id": item["item_id"], "quantity": int(arguments["quantity"]), "total_quantity": item["quantity"]},
            source_turn_id=context.turn_id,
        )
        return ToolExecutionResult(ok=True, result={**item, "world_event": event})


class EmitWorldEventTool:
    spec = ToolSpec(
        name="emit_world_event",
        description="Emit a validated world event without changing another state table.",
        argument_schema={
            "type": "object",
            "properties": {
                "event_type": {"type": "string"},
                "payload": {"type": "object"},
                "player_visible": {"type": "boolean"},
            },
            "required": ["event_type", "payload"],
        },
        read_only=False,
    )

    def __init__(self, state: GameStateBackend):
        self.state = state

    def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        event = self.state.log_world_event(
            event_type=arguments["event_type"],
            npc_id=context.npc_id,
            player_id=context.player_id,
            payload=arguments["payload"],
            source_turn_id=context.turn_id,
            player_visible=bool(arguments.get("player_visible", True)),
        )
        return ToolExecutionResult(ok=True, result={"world_event": event})


def create_default_registry(state: GameStateBackend | None = None) -> ToolRegistry:
    state = state or StateStore()
    return ToolRegistry(
        [
            GetPlayerStateTool(state),
            GetQuestStateTool(state),
            StartQuestTool(state),
            AdvanceQuestTool(state),
            UpdateRelationshipTool(state),
            GrantItemTool(state),
            EmitWorldEventTool(state),
        ]
    )
