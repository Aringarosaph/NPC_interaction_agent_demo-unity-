from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
import yaml

from .config import DATA_ROOT


@dataclass
class NpcBundle:
    profile: Dict[str, Any]
    chunks: List[Dict[str, Any]]
    examples: Dict[str, Any]
    memory_seed: Dict[str, Any]


class DataLoader:
    def __init__(self, data_root: Path = DATA_ROOT):
        self.data_root = Path(data_root)
        self.npc_root = self.data_root / "npcs"
        self._bundles: Dict[str, NpcBundle] = {}

    def load_all(self) -> Dict[str, NpcBundle]:
        index_path = self.npc_root / "index.yaml"
        index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
        for item in index["npcs"]:
            npc_id = item["npc_id"]
            base = self.npc_root / npc_id
            profile = self._read_yaml(base / "profile.yaml")
            chunks_pack = self._read_yaml(base / "knowledge_chunks.yaml")
            examples = self._read_yaml(base / "dialogue_examples.yaml")
            memory_seed = self._read_yaml(base / "memory_seed.yaml")
            self._bundles[npc_id] = NpcBundle(
                profile=profile,
                chunks=chunks_pack.get("chunks", []),
                examples=examples,
                memory_seed=memory_seed,
            )
        return self._bundles

    def get_bundle(self, npc_id: str) -> NpcBundle:
        if not self._bundles:
            self.load_all()
        if npc_id not in self._bundles:
            raise KeyError(f"Unknown npc_id: {npc_id}")
        return self._bundles[npc_id]

    @staticmethod
    def _read_yaml(path: Path) -> Dict[str, Any]:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
