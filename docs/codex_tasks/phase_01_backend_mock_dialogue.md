# Phase 01 - 后端 Mock 对话跑通

目标：不接 DeepSeek，先让 Unity/HTTP 全链路可用。

任务：
1. 设置 `.env` 中 `MOCK_LLM_WHEN_NO_KEY=true`，留空 `DEEPSEEK_API_KEY`。
2. 调用 `POST /api/v1/dialogue`。
3. 验证三个 NPC 均返回至少一句话。
4. 验证跨世界问题命中 boundary chunk。
5. 在响应 debug 中尽量填入 `used_knowledge_ids`。

测试输入：
- 阿米娅：`你知道八重神子吗？`
- 八重神子：`我想投稿轻小说。`
- 今汐：`我有一个愿望。`

验收：
- curl 能返回 `dialogue_response.v1`。
- 每个 response 的 `utterances` 数量在 1-3。
- 后端没有异常。


通用约束：
- 不改 `schemas/` 中已冻结字段名。
- 不把 Unity 客户端直接连 DeepSeek；必须通过本地 FastAPI。
- NPC 回复必须是 1-3 句短气泡，不允许长段落。
- 角色不知道其他作品世界、Unity、AI、后端。
- 先保证可跑，再优化表现。
