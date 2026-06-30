from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

from .models import MemorySnippet, MemoryDebugRecord
from .config import BACKEND_DIR


class MemoryStore:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or (BACKEND_DIR / "local_memory.sqlite")
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
              memory_id TEXT PRIMARY KEY,
              npc_id TEXT NOT NULL,
              player_id TEXT NOT NULL,
              memory_type TEXT NOT NULL,
              summary TEXT NOT NULL,
              detail TEXT NOT NULL,
              salience REAL NOT NULL,
              confidence REAL NOT NULL,
              created_at TEXT NOT NULL,
              last_seen_at TEXT NOT NULL,
              decay_policy TEXT NOT NULL,
              expires_at TEXT,
              source_turn_id TEXT,
              write_protected INTEGER NOT NULL,
              visibility TEXT NOT NULL,
              retrieval_keywords TEXT NOT NULL,
              status TEXT NOT NULL
            )
            """
        )
        columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(memories)").fetchall()}
        if "visibility" not in columns:
            self.conn.execute("ALTER TABLE memories ADD COLUMN visibility TEXT NOT NULL DEFAULT '{}'")
        self.conn.commit()

    def seed_from_pack(self, seed_pack: Dict[str, Any]) -> None:
        for r in seed_pack.get("records", []):
            self.upsert_record(r)

    def close(self) -> None:
        self.conn.close()

    def upsert_record(self, r: Dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO memories VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                r["memory_id"], r["npc_id"], r["player_id"], r["memory_type"], r["summary"], r["detail"],
                float(r["salience"]), float(r["confidence"]), r["created_at"], r["last_seen_at"], r["decay_policy"],
                r.get("expires_at"), r.get("source_turn_id"), 1 if r.get("write_protected") else 0,
                json.dumps(r.get("visibility", {}), ensure_ascii=False),
                json.dumps(r.get("retrieval_keywords", []), ensure_ascii=False), r.get("status", "active")
            ),
        )
        self.conn.commit()

    def search(self, npc_id: str, player_id: str, query: str, limit: int = 3) -> List[MemorySnippet]:
        rows = self.conn.execute(
            """
            SELECT * FROM memories
            WHERE npc_id = ? AND status = 'active' AND (player_id = ? OR player_id = '__default__')
            """,
            (npc_id, player_id),
        ).fetchall()
        q = query.lower()
        query_tokens = self._query_tokens(q)
        scored = []
        for row in rows:
            keywords = self._json_list(row["retrieval_keywords"])
            text = " ".join([row["summary"], row["detail"], " ".join(keywords)]).lower()
            score = 0.0
            for keyword in keywords:
                if keyword and keyword.lower() in q:
                    score += 2.0
            for token in query_tokens:
                if token and token in text:
                    score += 1.0
            score += float(row["salience"]) * 0.2
            scored.append((score, row))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [MemorySnippet(memory_id=r["memory_id"], summary=r["summary"], detail=r["detail"], score=s) for s, r in scored[:limit]]

    def list_records(self, npc_id: str, player_id: str, include_default: bool = True) -> List[MemoryDebugRecord]:
        if include_default:
            rows = self.conn.execute(
                """
                SELECT * FROM memories
                WHERE npc_id = ? AND status = 'active' AND (player_id = ? OR player_id = '__default__')
                ORDER BY write_protected ASC, salience DESC, last_seen_at DESC
                """,
                (npc_id, player_id),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """
                SELECT * FROM memories
                WHERE npc_id = ? AND player_id = ? AND status = 'active'
                ORDER BY salience DESC, last_seen_at DESC
                """,
                (npc_id, player_id),
            ).fetchall()
        return [self._row_to_debug_record(row) for row in rows]

    def write_candidate(self, npc_id: str, player_id: str, candidate: Dict[str, Any], source_turn_id: str) -> str | None:
        if not candidate or not candidate.get("summary"):
            return None
        memory_type = candidate.get("memory_type", "fact")
        if memory_type not in {"promise", "preference", "relationship", "event", "fact"}:
            return None
        now = datetime.now(timezone.utc).isoformat()
        memory_id = candidate.get("memory_id") or f"mem_{npc_id}_{uuid.uuid4().hex[:12]}"
        record = {
            "memory_id": memory_id,
            "npc_id": npc_id,
            "player_id": player_id,
            "memory_type": memory_type,
            "summary": candidate.get("summary", "")[:120],
            "detail": candidate.get("detail", candidate.get("summary", ""))[:300],
            "salience": float(candidate.get("salience", 0.5)),
            "confidence": 0.75,
            "created_at": now,
            "last_seen_at": now,
            "decay_policy": "never",
            "expires_at": None,
            "source_turn_id": source_turn_id,
            "write_protected": False,
            "visibility": {"owner_npc_only": True, "share_with_world_ids": []},
            "retrieval_keywords": candidate.get("retrieval_keywords", []),
            "status": "active",
        }
        self.upsert_record(record)
        return memory_id

    @staticmethod
    def _query_tokens(q: str) -> List[str]:
        return [t for t in q.replace("，", " ").replace("。", " ").replace("？", " ").replace("！", " ").split() if t]

    @staticmethod
    def _json_list(raw: str) -> List[str]:
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return []
        return value if isinstance(value, list) else []

    @staticmethod
    def _json_dict(raw: str) -> Dict[str, Any]:
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    def _row_to_debug_record(self, row: sqlite3.Row) -> MemoryDebugRecord:
        return MemoryDebugRecord(
            memory_id=row["memory_id"],
            npc_id=row["npc_id"],
            player_id=row["player_id"],
            memory_type=row["memory_type"],
            summary=row["summary"],
            detail=row["detail"],
            salience=float(row["salience"]),
            confidence=float(row["confidence"]),
            created_at=row["created_at"],
            last_seen_at=row["last_seen_at"],
            decay_policy=row["decay_policy"],
            expires_at=row["expires_at"],
            source_turn_id=row["source_turn_id"],
            write_protected=bool(row["write_protected"]),
            visibility=self._json_dict(row["visibility"]),
            retrieval_keywords=self._json_list(row["retrieval_keywords"]),
            status=row["status"],
        )
