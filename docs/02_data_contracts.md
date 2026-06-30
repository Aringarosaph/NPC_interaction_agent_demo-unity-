# 02 数据契约冻结

本项目所有核心字段名冻结在 `schemas/` 中。Codex 实现时不要随意改字段名。

## NpcProfile

文件：`data/npcs/{npc_id}/profile.yaml`

用途：锁定 NPC 是谁、怎么说话、知道什么边界。Profile 常驻 prompt，不进入检索排序。

关键字段：

- `npc_id`：稳定 ID，如 `arknights_amiya`。
- `world_id`：世界 ID，用于阻断跨作品串知识。
- `identity.canonical_role`：角色身份。
- `identity.player_address_default`：默认称呼玩家。
- `persona.core_traits`：性格。
- `speech.sentence_max_chars`：每句最大长度。
- `speech.utterance_count.max`：每轮最多几句。
- `knowledge_policy.forbidden_scopes`：禁止回答范围。
- `generation_policy.llm_temperature`：每个 NPC 可不同。

## KnowledgeChunk

文件：`data/npcs/{npc_id}/knowledge_chunks.yaml`

用途：RAG 检索内容。所有知识必须有 `npc_id` 和 `world_id`，检索前必须过滤。

关键字段：

- `chunk_id`：唯一 ID，会记录在 debug 中。
- `scope`：`self_profile | world_common | faction | relationship | ability | plot_safe | demo_control | boundary`。
- `visibility.npc_ids`：哪些 NPC 可见。
- `visibility.spoiler_level`：剧透等级，MVP 默认允许 0-1。
- `retrieval_text`：用于检索的事实摘要。
- `npc_sayable`：NPC 可自然说出的改写版本。
- `source_refs`：留档来源，不展示给玩家。

## MemoryRecord

文件/数据库：seed 在 YAML，运行时写入 SQLite。

用途：记录玩家和某 NPC 的关系变化，而不是世界观事实。

只写这些：

- 玩家明确偏好。
- 玩家承诺。
- 玩家告诉 NPC 的个人信息。
- 玩家和 NPC 的重要共同事件。
- NPC 对玩家态度明显变化。

不要写这些：

- 官方设定。
- 检索知识块内容。
- 系统提示。
- “玩家在 Unity 里测试”这类元信息。

## DialogueRequest

Unity 发送：

```json
{
  "schema_version": "dialogue_request.v1",
  "session_id": "local_session_001",
  "player_id": "local_player",
  "npc_id": "arknights_amiya",
  "player_text": "你知道八重神子吗？",
  "distance_m": 2.1,
  "is_in_range": true,
  "world_state": {
    "location_id": "portfolio_whitebox_room",
    "game_time_label": "demo",
    "quest_stage": 0,
    "relationship_score": 0,
    "debug_enabled": true
  }
}
```

## DialogueResponse

后端返回：

```json
{
  "schema_version": "dialogue_response.v1",
  "turn_id": "turn_xxx",
  "npc_id": "arknights_amiya",
  "utterances": [
    {"text": "抱歉，博士。", "emotion": "cautious", "action": "look_at_player", "delay_ms": 400},
    {"text": "罗德岛没有这份档案。", "emotion": "neutral", "action": "idle", "delay_ms": 650}
  ],
  "internal": {
    "used_knowledge_ids": ["amiya_boundary_other_worlds"],
    "used_memory_ids": [],
    "memory_candidates": [],
    "confidence": 0.82
  }
}
```
