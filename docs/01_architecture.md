# 01 架构方案

## 最小架构

```text
Unity Client
  ├─ PlayerController / 白盒主角
  ├─ NpcAgentMarker / 三个 NPC 白模
  ├─ DialogueRangeDetector / 距离检测
  ├─ PlayerChatInput / 输入框发送
  ├─ SpeechBubbleController / 玩家与 NPC 气泡
  └─ NpcDialogueClient / HTTP 调后端

Local FastAPI Backend
  ├─ /api/v1/dialogue
  ├─ ProfileLoader: 读取 profile.yaml
  ├─ KnowledgeLoader: 读取 knowledge_chunks.yaml
  ├─ SmallKnowledgeRetriever: TF-IDF 字符 ngram 检索
  ├─ MemoryStore: SQLite 本地记忆
  ├─ PromptBuilder: 组装 profile + top chunks + memories
  ├─ LlmClient: DeepSeek JSON Output / Mock fallback
  └─ ResponseNormalizer: 限制 1-3 句、每句长度、情绪动作枚举
```

## 为什么不用复杂后端

作品集 demo 的知识量只有三个角色，每个角色 10-20 条知识块。使用本地 FastAPI + YAML + SQLite 足够展示完整链路。

向量数据库、reranker、分布式服务、权限中心可以作为“未来扩展”讲，但不应成为 MVP 阻塞项。

## 对话时序

```text
1. Unity 检测玩家当前最近 NPC，且距离 <= interaction_radius_m。
2. 玩家发送输入。
3. Unity 显示玩家气泡。
4. Unity POST /api/v1/dialogue。
5. 后端加载 npc profile。
6. 后端过滤该 npc 可见 knowledge chunks。
7. 后端用玩家输入 + 最近对话检索 top_k chunks。
8. 后端检索该 player_id + npc_id 的记忆。
9. 后端构造 prompt，调用 DeepSeek 或 mock。
10. 后端校验 JSON，裁剪为 1-3 条 utterances。
11. Unity 收到 utterances，按 delay_ms 逐句显示 NPC 气泡。
12. 后端保存本轮对话与可选记忆。
```

## MVP 选择

MVP 不使用 SSE。后端一次返回完整 JSON，Unity 负责逐句播放。这比流式更稳定，也更适合求职作品集快速落地。

后期可选升级：`/api/v1/dialogue/stream` 使用 SSE，一句一句推送给 Unity。
