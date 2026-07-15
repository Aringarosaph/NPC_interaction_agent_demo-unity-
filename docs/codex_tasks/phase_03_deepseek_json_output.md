# Phase 03 - 接入 DeepSeek JSON 输出

目标：使用 DeepSeek-V4-Flash 生成结构化短句回复。

任务：
1. 在 `.env` 中配置 `DEEPSEEK_API_KEY`。
2. 使用 OpenAI SDK compatible client：`base_url=https://api.deepseek.com`。
3. 调用 chat completions：`model=deepseek-v4-flash`。
4. 设置 `response_format={"type":"json_object"}`。
5. 在 prompt 中明确写出 json 输出格式。
6. 设置 `extra_body={"thinking": {"type":"disabled"}}`。
7. 如果 JSON 解析失败，落到 mock/unknown fallback。

验收：
- 10 次连续请求不崩溃。
- 回复是 JSON，可被 `ResponseNormalizer` 解析。
- NPC 不输出 Markdown 或解释文字。
- 每句 <= 28 字左右。


通用约束：
- 不改 `schemas/` 中已冻结字段名。
- 不把 Unity 客户端直接连 DeepSeek；必须通过本地 FastAPI。
- NPC 回复必须是 1-3 句短气泡，不允许长段落。
- 角色不知道其他作品世界、Unity、AI、后端。
- 先保证可跑，再优化表现。
