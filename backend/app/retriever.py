from __future__ import annotations

from typing import Any, Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import RetrievedChunk

CROSS_WORLD_KEYWORDS = {
    "arknights_amiya": ["八重", "神子", "原神", "稻妻", "今汐", "鸣潮", "今州", "Unity", "AI", "模型", "后端"],
    "genshin_yae_miko": ["阿米娅", "罗德岛", "明日方舟", "泰拉", "今汐", "鸣潮", "今州", "Unity", "AI", "模型", "后端"],
    "wuwa_jinhsi": ["阿米娅", "罗德岛", "明日方舟", "八重", "神子", "原神", "稻妻", "Unity", "AI", "模型", "后端"],
}


class SmallKnowledgeRetriever:
    def __init__(self, chunks_by_npc: Dict[str, List[Dict[str, Any]]], top_k: int = 4, min_score: float = 0.035):
        self.chunks_by_npc = chunks_by_npc
        self.top_k = top_k
        self.min_score = min_score
        self.vectorizers: Dict[str, TfidfVectorizer] = {}
        self.matrices: Dict[str, Any] = {}
        self.indexed_chunks: Dict[str, List[Dict[str, Any]]] = {}
        self._build()

    def _build(self) -> None:
        for npc_id, chunks in self.chunks_by_npc.items():
            corpus = [self._chunk_text(c) for c in chunks]
            if not corpus:
                continue
            vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), lowercase=True)
            matrix = vectorizer.fit_transform(corpus)
            self.vectorizers[npc_id] = vectorizer
            self.matrices[npc_id] = matrix
            self.indexed_chunks[npc_id] = list(chunks)

    def retrieve(self, npc_id: str, query: str, quest_stage: int = 0, max_spoiler_level: int = 1) -> List[RetrievedChunk]:
        chunks = self._visible_chunks(npc_id, quest_stage, max_spoiler_level)
        if not chunks:
            return []

        # Force boundary chunks when the player asks cross-world or meta questions.
        boundary_hits = []
        if any(k.lower() in query.lower() for k in CROSS_WORLD_KEYWORDS.get(npc_id, [])):
            boundary_hits = [c for c in chunks if c.get("scope") == "boundary"]

        vectorizer = self.vectorizers[npc_id]
        matrix = self.matrices[npc_id]
        qv = vectorizer.transform([query])
        scores = cosine_similarity(qv, matrix)[0]
        score_by_chunk_id = {
            c["chunk_id"]: float(score)
            for c, score in zip(self.indexed_chunks[npc_id], scores)
        }

        ranked = sorted(
            ((c, score_by_chunk_id.get(c["chunk_id"], 0.0)) for c in chunks),
            key=lambda x: (x[1], x[0].get("priority", 0)),
            reverse=True,
        )
        selected = []
        seen = set()
        for c in boundary_hits:
            selected.append(self._to_result(c, 1.0))
            seen.add(c["chunk_id"])
        for c, score in ranked:
            if c["chunk_id"] in seen:
                continue
            if score < self.min_score and len(selected) > 0:
                continue
            selected.append(self._to_result(c, float(score)))
            if len(selected) >= self.top_k:
                break
        return selected[: self.top_k]

    def _visible_chunks(self, npc_id: str, quest_stage: int, max_spoiler_level: int) -> List[Dict[str, Any]]:
        visible = []
        for c in self.chunks_by_npc.get(npc_id, []):
            v = c.get("visibility", {})
            if npc_id not in v.get("npc_ids", []):
                continue
            if quest_stage < int(v.get("player_quest_stage_min", 0)):
                continue
            if int(v.get("spoiler_level", 0)) > max_spoiler_level:
                continue
            visible.append(c)
        return visible

    @staticmethod
    def _chunk_text(chunk: Dict[str, Any]) -> str:
        parts = [chunk.get("title", ""), chunk.get("retrieval_text", ""), " ".join(chunk.get("keywords", [])), " ".join(chunk.get("tags", []))]
        return "\n".join(parts)

    @staticmethod
    def _to_result(chunk: Dict[str, Any], score: float) -> RetrievedChunk:
        return RetrievedChunk(
            chunk_id=chunk["chunk_id"],
            title=chunk.get("title", ""),
            retrieval_text=chunk.get("retrieval_text", ""),
            npc_sayable=chunk.get("npc_sayable", []),
            score=score,
        )
