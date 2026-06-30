# Phase 02 - 小型 RAG 检索与 Debug

目标：让检索结果可解释，便于面试展示。

任务：
1. 完善 `SmallKnowledgeRetriever`。
2. 输入 query 后返回 top_k chunk。
3. API 响应的 `internal.used_knowledge_ids` 显示命中的 chunk_id。
4. 添加 `/api/v1/debug/retrieve?npc_id=...&q=...` 便于调试。
5. 添加 pytest：源石病、轻小说、愿望、跨世界问题。

验收：
- `源石病` 命中 `amiya_oripathy_infected`。
- `轻小说投稿` 命中 `yae_publishing_house`。
- `今州愿望` 命中 `jinhsi_wish_custom`。
- `阿米娅认识八重神子吗` 命中 `amiya_boundary_other_worlds`。


通用约束：
- 不改 `schemas/` 中已冻结字段名。
- 不把 Unity 客户端直接连 DeepSeek；必须通过本地 FastAPI。
- NPC 回复必须是 1-3 句短气泡，不允许长段落。
- 角色不知道其他作品世界、Unity、AI、后端。
- 先保证可跑，再优化表现。
