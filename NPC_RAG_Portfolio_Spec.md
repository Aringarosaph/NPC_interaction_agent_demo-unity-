# NPC RAG Agent 作品集方案总览

本方案服务于一个小型求职作品集：Unity 白盒场景中，玩家靠近三个 NPC 并通过输入框对话；本地后端使用数据驱动 profile、小型 RAG 检索和 DeepSeek JSON 输出，让 NPC 以 1-3 个短气泡回应。

## 冻结技术路线

- Unity：白盒场景、输入框、距离检测、气泡 UI。
- 后端：本地 FastAPI。
- RAG：YAML 知识块 + TF-IDF 字符 ngram 检索。
- 记忆：SQLite 本地 player_id + npc_id 记忆。
- LLM：DeepSeek-V4-Flash，JSON Output，thinking disabled。
- 输出：`DialogueResponse` 中的 `utterances` 数组，Unity 逐句播放。

## 冻结数据类型

详见 `schemas/`：

- `npc_profile.v1`
- `knowledge_chunk.v1`
- `memory_record.v1`
- `dialogue_request.v1`
- `dialogue_response.v1`

## 三个 NPC

- `arknights_amiya`：温和、负责、谨慎，称玩家为博士，知识范围限罗德岛/感染者/源石相关。
- `genshin_yae_miko`：优雅、狡黠、调侃，称玩家小家伙/旅行者，知识范围限鸣神大社/八重堂/稻妻相关。
- `wuwa_jinhsi`：端庄、温和、治理者视角，称玩家贵客/漂泊者，知识范围限今州/愿望/岁主角相关。

## 最小验收

- 三个 NPC 都能对话。
- 每次回复 1-3 句。
- 跨世界问题不串台。
- Debug 能看到命中 knowledge chunk。
- 至少一个偏好记忆能写入并回忆。

更多细节见 `docs/` 和 `codex_tasks/`。
