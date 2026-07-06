from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from .base import ToolExecutionContext, ToolExecutionResult, ToolSpec
from .registry import ToolRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class InMemoryGameState:
    player_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    quest_states: Dict[Tuple[str, str], Dict[str, Any]] = field(default_factory=dict)
    relationships: Dict[Tuple[str, str], Dict[str, Any]] = field(default_factory=dict)
    inventory: Dict[Tuple[str, str], Dict[str, Any]] = field(default_factory=dict)
    world_events: list[Dict[str, Any]] = field(default_factory=list)

    def player_state(self, player_id: str) -> Dict[str, Any]:
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
        description="Read the current lightweight player state.",
        argument_schema={"type": "object", "properties": {}, "required": []},
        read_only=True,
    )

    def __init__(self, state: InMemoryGameState):
        self.state = state

    def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        return ToolExecutionResult(ok=True, result=dict(self.state.player_state(context.player_id)))


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

    def __init__(self, state: InMemoryGameState):
        self.state = state

    def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        quest_id = arguments["quest_id"]
        record = self.state.quest_states.get((context.player_id, quest_id))
        if record is None:
            record = {
                "quest_id": quest_id,
                "player_id": context.player_id,
                "npc_id": context.npc_id,
                "stage": 0,
                "status": "not_started",
                "updated_at": None,
            }
        return ToolExecutionResult(ok=True, result=dict(record))


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

    def __init__(self, state: InMemoryGameState):
        self.state = state

    def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        quest_id = arguments["quest_id"]
        key = (context.player_id, quest_id)
        record = self.state.quest_states.get(key)
        if record is None:
            record = {
                "quest_id": quest_id,
                "player_id": context.player_id,
                "npc_id": context.npc_id,
                "stage": 1,
                "status": "active",
                "updated_at": _now(),
                "source_turn_id": context.turn_id,
            }
            self.state.quest_states[key] = record
        elif record.get("status") == "not_started":
            record.update({"stage": 1, "status": "active", "updated_at": _now(), "source_turn_id": context.turn_id})

        event = _world_event(
            event_type="quest_started",
            npc_id=context.npc_id,
            player_id=context.player_id,
            payload={"quest_id": quest_id, "stage": record["stage"], "status": record["status"]},
            source_turn_id=context.turn_id,
        )
        self.state.world_events.append(event)
        return ToolExecutionResult(ok=True, result={**record, "world_event": event})


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

    def __init__(self, state: InMemoryGameState):
        self.state = state

    def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        quest_id = arguments["quest_id"]
        key = (context.player_id, quest_id)
        record = self.state.quest_states.get(key)
        if record is None or record.get("status") == "not_started":
            return ToolExecutionResult(ok=False, error=f"quest is not active: {quest_id}")

        expected_stage = arguments.get("expected_stage")
        if expected_stage is not None and record.get("stage") != expected_stage:
            return ToolExecutionResult(
                ok=False,
                error=f"quest stage mismatch: expected {expected_stage}, got {record.get('stage')}",
            )

        record["stage"] = int(record.get("stage", 0)) + 1
        record["status"] = "completed" if record["stage"] >= 2 else "active"
        record["updated_at"] = _now()
        record["source_turn_id"] = context.turn_id

        event = _world_event(
            event_type="quest_advanced",
            npc_id=context.npc_id,
            player_id=context.player_id,
            payload={"quest_id": quest_id, "stage": record["stage"], "status": record["status"]},
            source_turn_id=context.turn_id,
        )
        self.state.world_events.append(event)
        return ToolExecutionResult(ok=True, result={**record, "world_event": event})


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

    def __init__(self, state: InMemoryGameState):
        self.state = state

    def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        key = (context.npc_id, context.player_id)
        record = self.state.relationships.setdefault(
            key,
            {
                "npc_id": context.npc_id,
                "player_id": context.player_id,
                "relationship_score": 0.0,
                "relationship_label": "neutral",
                "updated_at": _now(),
            },
        )
        record["relationship_score"] = float(record["relationship_score"]) + float(arguments["delta"])
        record["relationship_label"] = _relationship_label(record["relationship_score"])
        record["updated_at"] = _now()
        record["reason"] = arguments.get("reason", "")

        event = _world_event(
            event_type="relationship_changed",
            npc_id=context.npc_id,
            player_id=context.player_id,
            payload={
                "relationship_score": record["relationship_score"],
                "relationship_label": record["relationship_label"],
                "delta": float(arguments["delta"]),
            },
            source_turn_id=context.turn_id,
        )
        self.state.world_events.append(event)
        return ToolExecutionResult(ok=True, result={**record, "world_event": event})


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

    def __init__(self, state: InMemoryGameState):
        self.state = state

    def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        quantity = int(arguments["quantity"])
        if quantity <= 0:
            return ToolExecutionResult(ok=False, error="quantity must be positive")

        item_id = arguments["item_id"]
        key = (context.player_id, item_id)
        record = self.state.inventory.setdefault(
            key,
            {
                "player_id": context.player_id,
                "item_id": item_id,
                "quantity": 0,
                "source_turn_id": context.turn_id,
                "updated_at": _now(),
            },
        )
        record["quantity"] = int(record["quantity"]) + quantity
        record["source_turn_id"] = context.turn_id
        record["updated_at"] = _now()

        event = _world_event(
            event_type="item_granted",
            npc_id=context.npc_id,
            player_id=context.player_id,
            payload={"item_id": item_id, "quantity": quantity, "total_quantity": record["quantity"]},
            source_turn_id=context.turn_id,
        )
        self.state.world_events.append(event)
        return ToolExecutionResult(ok=True, result={**record, "world_event": event})


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

    def __init__(self, state: InMemoryGameState):
        self.state = state

    def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        event = _world_event(
            event_type=arguments["event_type"],
            npc_id=context.npc_id,
            player_id=context.player_id,
            payload=arguments["payload"],
            source_turn_id=context.turn_id,
            player_visible=bool(arguments.get("player_visible", True)),
        )
        self.state.world_events.append(event)
        return ToolExecutionResult(ok=True, result={"world_event": event})


def create_default_registry(state: InMemoryGameState | None = None) -> ToolRegistry:
    state = state or InMemoryGameState()
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


def _world_event(
    event_type: str,
    npc_id: str,
    player_id: str,
    payload: Dict[str, Any],
    source_turn_id: str,
    player_visible: bool = True,
) -> Dict[str, Any]:
    return {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "event_type": event_type,
        "npc_id": npc_id,
        "player_id": player_id,
        "payload": payload,
        "player_visible": player_visible,
        "created_at": _now(),
        "source_turn_id": source_turn_id,
    }


def _relationship_label(score: float) -> str:
    if score >= 20:
        return "trusted"
    if score >= 5:
        return "friendly"
    if score <= -10:
        return "strained"
    return "neutral"
