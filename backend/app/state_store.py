from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .config import BACKEND_DIR


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


class StateStore:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or (BACKEND_DIR / "local_state.sqlite")
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def close(self) -> None:
        self.conn.close()

    def _init_db(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS player_states (
              player_id TEXT PRIMARY KEY,
              current_location_id TEXT,
              created_at TEXT,
              updated_at TEXT
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS npc_relationships (
              npc_id TEXT,
              player_id TEXT,
              relationship_score REAL,
              relationship_label TEXT,
              updated_at TEXT,
              PRIMARY KEY(npc_id, player_id)
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quest_states (
              quest_id TEXT,
              player_id TEXT,
              npc_id TEXT,
              stage INTEGER,
              status TEXT,
              updated_at TEXT,
              PRIMARY KEY(quest_id, player_id)
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_items (
              player_id TEXT,
              item_id TEXT,
              quantity INTEGER,
              source_turn_id TEXT,
              updated_at TEXT,
              PRIMARY KEY(player_id, item_id)
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS world_events (
              event_id TEXT PRIMARY KEY,
              event_type TEXT,
              npc_id TEXT,
              player_id TEXT,
              payload TEXT,
              player_visible INTEGER,
              created_at TEXT,
              source_turn_id TEXT
            )
            """
        )
        self.conn.commit()

    def get_player_snapshot(self, player_id: str, npc_id: str) -> Dict[str, Any]:
        player = self._ensure_player(player_id)
        relationship = self._get_relationship(npc_id, player_id)
        quests = [
            self._row_to_quest(row)
            for row in self.conn.execute(
                """
                SELECT * FROM quest_states
                WHERE player_id = ?
                ORDER BY updated_at DESC
                """,
                (player_id,),
            ).fetchall()
        ]
        inventory = [
            self._row_to_inventory(row)
            for row in self.conn.execute(
                """
                SELECT * FROM inventory_items
                WHERE player_id = ?
                ORDER BY updated_at DESC
                """,
                (player_id,),
            ).fetchall()
        ]
        recent_events = [
            self._row_to_event(row)
            for row in self.conn.execute(
                """
                SELECT * FROM world_events
                WHERE player_id = ?
                ORDER BY created_at DESC
                LIMIT 10
                """,
                (player_id,),
            ).fetchall()
        ]
        return {
            "player": player,
            "relationship": relationship,
            "quests": quests,
            "inventory": inventory,
            "recent_world_events": recent_events,
        }

    def get_quest_state(self, player_id: str, quest_id: str) -> Dict[str, Any]:
        row = self.conn.execute(
            """
            SELECT * FROM quest_states
            WHERE player_id = ? AND quest_id = ?
            """,
            (player_id, quest_id),
        ).fetchone()
        if row is None:
            return {
                "quest_id": quest_id,
                "player_id": player_id,
                "npc_id": "",
                "stage": 0,
                "status": "not_started",
                "updated_at": None,
            }
        return self._row_to_quest(row)

    def start_quest(self, player_id: str, npc_id: str, quest_id: str) -> Dict[str, Any]:
        self._ensure_player(player_id)
        existing = self.get_quest_state(player_id, quest_id)
        if existing["status"] != "not_started":
            return existing

        now = _now()
        self.conn.execute(
            """
            INSERT OR REPLACE INTO quest_states
            (quest_id, player_id, npc_id, stage, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (quest_id, player_id, npc_id, 1, "active", now),
        )
        self.conn.commit()
        return self.get_quest_state(player_id, quest_id)

    def advance_quest(
        self,
        player_id: str,
        npc_id: str,
        quest_id: str,
        expected_stage: int | None = None,
    ) -> Dict[str, Any]:
        self._ensure_player(player_id)
        existing = self.get_quest_state(player_id, quest_id)
        if existing["status"] == "not_started":
            raise ValueError(f"quest is not active: {quest_id}")
        if expected_stage is not None and existing["stage"] != expected_stage:
            raise ValueError(f"quest stage mismatch: expected {expected_stage}, got {existing['stage']}")

        stage = int(existing["stage"]) + 1
        status = "completed" if stage >= 2 else "active"
        now = _now()
        self.conn.execute(
            """
            UPDATE quest_states
            SET npc_id = ?, stage = ?, status = ?, updated_at = ?
            WHERE player_id = ? AND quest_id = ?
            """,
            (npc_id, stage, status, now, player_id, quest_id),
        )
        self.conn.commit()
        return self.get_quest_state(player_id, quest_id)

    def update_relationship(self, player_id: str, npc_id: str, delta: float, reason: str = "") -> Dict[str, Any]:
        self._ensure_player(player_id)
        existing = self._get_relationship(npc_id, player_id)
        score = float(existing["relationship_score"]) + float(delta)
        label = _relationship_label(score)
        now = _now()
        self.conn.execute(
            """
            INSERT OR REPLACE INTO npc_relationships
            (npc_id, player_id, relationship_score, relationship_label, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (npc_id, player_id, score, label, now),
        )
        self.conn.commit()
        record = self._get_relationship(npc_id, player_id)
        record["delta"] = float(delta)
        record["reason"] = reason
        return record

    def grant_item(self, player_id: str, item_id: str, quantity: int, source_turn_id: str) -> Dict[str, Any]:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self._ensure_player(player_id)
        row = self.conn.execute(
            """
            SELECT * FROM inventory_items
            WHERE player_id = ? AND item_id = ?
            """,
            (player_id, item_id),
        ).fetchone()
        total = quantity if row is None else int(row["quantity"]) + quantity
        now = _now()
        self.conn.execute(
            """
            INSERT OR REPLACE INTO inventory_items
            (player_id, item_id, quantity, source_turn_id, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (player_id, item_id, total, source_turn_id, now),
        )
        self.conn.commit()
        return self._row_to_inventory(
            self.conn.execute(
                """
                SELECT * FROM inventory_items
                WHERE player_id = ? AND item_id = ?
                """,
                (player_id, item_id),
            ).fetchone()
        )

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
        self._ensure_player(player_id)
        event_id = event_id or f"evt_{uuid.uuid4().hex[:12]}"
        now = _now()
        self.conn.execute(
            """
            INSERT INTO world_events
            (event_id, event_type, npc_id, player_id, payload, player_visible, created_at, source_turn_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                event_type,
                npc_id,
                player_id,
                json.dumps(payload, ensure_ascii=False),
                1 if player_visible else 0,
                now,
                source_turn_id,
            ),
        )
        self.conn.commit()
        return self._row_to_event(
            self.conn.execute(
                """
                SELECT * FROM world_events
                WHERE event_id = ?
                """,
                (event_id,),
            ).fetchone()
        )

    def reset_runtime(self, player_id: str | None = None) -> Dict[str, int]:
        tables = [
            "world_events",
            "inventory_items",
            "quest_states",
            "npc_relationships",
            "player_states",
        ]
        counts: Dict[str, int] = {}
        for table in tables:
            if player_id:
                cursor = self.conn.execute(
                    f"DELETE FROM {table} WHERE player_id = ?",
                    (player_id,),
                )
            else:
                cursor = self.conn.execute(f"DELETE FROM {table}")
            counts[table] = int(cursor.rowcount)
        self.conn.commit()
        return counts

    def _ensure_player(self, player_id: str) -> Dict[str, Any]:
        row = self.conn.execute(
            """
            SELECT * FROM player_states
            WHERE player_id = ?
            """,
            (player_id,),
        ).fetchone()
        if row is None:
            now = _now()
            self.conn.execute(
                """
                INSERT INTO player_states
                (player_id, current_location_id, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (player_id, "portfolio_whitebox_room", now, now),
            )
            self.conn.commit()
            row = self.conn.execute(
                """
                SELECT * FROM player_states
                WHERE player_id = ?
                """,
                (player_id,),
            ).fetchone()
        return self._row_to_player(row)

    def _get_relationship(self, npc_id: str, player_id: str) -> Dict[str, Any]:
        row = self.conn.execute(
            """
            SELECT * FROM npc_relationships
            WHERE npc_id = ? AND player_id = ?
            """,
            (npc_id, player_id),
        ).fetchone()
        if row is None:
            return {
                "npc_id": npc_id,
                "player_id": player_id,
                "relationship_score": 0.0,
                "relationship_label": "neutral",
                "updated_at": None,
            }
        return self._row_to_relationship(row)

    @staticmethod
    def _row_to_player(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "player_id": row["player_id"],
            "current_location_id": row["current_location_id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _row_to_relationship(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "npc_id": row["npc_id"],
            "player_id": row["player_id"],
            "relationship_score": float(row["relationship_score"]),
            "relationship_label": row["relationship_label"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _row_to_quest(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "quest_id": row["quest_id"],
            "player_id": row["player_id"],
            "npc_id": row["npc_id"],
            "stage": int(row["stage"]),
            "status": row["status"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _row_to_inventory(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "player_id": row["player_id"],
            "item_id": row["item_id"],
            "quantity": int(row["quantity"]),
            "source_turn_id": row["source_turn_id"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> Dict[str, Any]:
        try:
            payload = json.loads(row["payload"])
        except json.JSONDecodeError:
            payload = {}
        return {
            "event_id": row["event_id"],
            "event_type": row["event_type"],
            "npc_id": row["npc_id"],
            "player_id": row["player_id"],
            "payload": payload,
            "player_visible": bool(row["player_visible"]),
            "created_at": row["created_at"],
            "source_turn_id": row["source_turn_id"],
        }
