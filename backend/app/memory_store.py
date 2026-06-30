from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

from .models import MemorySnippet
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
        scored = []
        for row in rows:
            text = " ".join([row["summary"], row["detail"], row["retrieval_keywords"]]).lower()
            score = 0.0
            for token in self._query_tokens(q):
                if token and token in text:
                    score += 1.0
            score += float(row["salience"]) * 0.2
            scored.append((score, row))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [MemorySnippet(memory_id=r["memory_id"], summary=r["summary"], detail=r["detail"], score=s) for s, r in scored[:limit]]

    def write_candidate(self, npc_id: str, player_id: str, candidate: Dict[str, Any], source_turn_id: str) -> str | None:
        if not candidate or not candidate.get("summary"):
            return None
        memory_type = candidate.get("memory_type", "fact")
        if memory_type not in {"promise", "preference", "relationship", "event", "fact"}:
            return None
        now = datetime.now(timezone.utc).isoformat()
        memory_id = f"mem_{npc_id}_{uuid.uuid4().hex[:12]}"
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
