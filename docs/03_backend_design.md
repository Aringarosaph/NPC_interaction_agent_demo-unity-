# 03 本地后端设计

## 技术选型

- Python 3.11+
- FastAPI
- Uvicorn
- PyYAML
- scikit-learn TF-IDF 检索
- SQLite 本地记忆
- OpenAI SDK 兼容调用 DeepSeek
- `.env` 管理 `DEEPSEEK_API_KEY`

## 为什么使用 TF-IDF 字符 ngram

三个 NPC 的知识库很小，使用本地 TF-IDF 字符 ngram 足以展示 RAG 检索。它没有外部向量模型下载成本，中文、英文、专名混合时也能靠字符片段命中。

可在简历中说明：

> MVP 使用本地轻量检索，保留向量检索接口，后续可替换为 Chroma/Qdrant + bge-small-zh。

## 模块职责

### DataLoader

读取：

- `data/npcs/index.yaml`
- `profile.yaml`
- `knowledge_chunks.yaml`
- `dialogue_examples.yaml`
- `memory_seed.yaml`

### SmallKnowledgeRetriever

输入：`npc_id`, `player_text`, `world_state`, `recent_turns`

步骤：

1. 只保留 `chunk.npc_id == npc_id`。
2. 只保留 `chunk.world_id == profile.world_id`。
3. 过滤 `quest_stage` 和 `spoiler_level`。
4. 用 TF-IDF 字符 ngram 排序。
5. 如果玩家问到其他世界关键词，优先 boundary chunk。
6. 返回 top_k。

### MemoryStore

SQLite 表：

```sql
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
  retrieval_keywords TEXT NOT NULL,
  status TEXT NOT NULL
);
```

### PromptBuilder

Prompt 顺序固定：

1. System template。
2. Profile summary。
3. Current state。
4. Recent dialogue。
5. Memory snippets。
6. Knowledge snippets。
7. Player input。

### LlmClient

DeepSeek 调用参数建议：

- model: `deepseek-v4-flash`
- thinking: disabled
- response_format: `{"type":"json_object"}`
- max_tokens: 360
- temperature: 从 profile 读取

如果没有 API key，使用 mock 返回，便于 Unity 先跑通。

### ResponseNormalizer

强制：

- 至少 1 句，最多 3 句。
- 单句超过 `sentence_max_chars` 时按标点拆分或截短。
- emotion/action 不在枚举内时改默认值。
- 空回复时回退到 unknown 策略。
