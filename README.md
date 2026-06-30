# 三 NPC 小型 RAG Agent 作品集工程包

这是一个面向求职作品集的最小可落地方案包：本地 FastAPI 后端 + 小型内存检索 + DeepSeek-V4-Flash JSON 输出 + Unity 白盒场景气泡对话。

## 目标效果

Unity 中放置三个白模 NPC：阿米娅、八重神子、今汐。玩家靠近 NPC 到一定范围内，在输入框发送文字后，主角头顶先显示玩家气泡；后端返回该 NPC 的 1-3 句短回复，Unity 按句显示 NPC 气泡。

## 包内内容

- `docs/`：架构、数据契约、后端、Unity、Prompt、评测与留档说明。
- `schemas/`：冻结的数据类型与字段名，供 Codex 和代码校验使用。
- `data/npcs/`：三个 NPC 的 profile、knowledge chunks、dialogue examples、memory seed。
- `prompts/`：系统提示词、上下文模板、记忆提取模板。
- `backend/`：本地 FastAPI 后端骨架。
- `unity_scaffold/`：Unity C# 脚本骨架。
- `unity/PortfolioNpcRagWhitebox/`：Unity 6000.4.2f1 白盒工程，已生成可验证场景。
- `codex_tasks/`：可直接交给 Codex 分阶段执行的任务文件。
- `eval/`：人设、知识边界、短句输出、记忆测试用例。

## 当前可运行状态

- 后端已支持 RAG 检索、DeepSeek JSON 回复、本地 SQLite 记忆和调试接口。
- Unity 白盒工程已生成 `Assets/Scenes/Scene_PortfolioNpcRag.unity`。
- Unity 场景包含地板、主角胶囊、三个 NPC 胶囊、第三视角相机、对话输入 UI、玩家/NPC 气泡和本地后端 endpoint。
- Unity 缓存、日志、临时文件和用户设置被 `.gitignore` 排除。

## 推荐实现顺序

1. 跑通 `backend/` 的 mock LLM。
2. 让 Unity 输入框调用 `POST /api/v1/dialogue` 并显示气泡。
3. 接入 DeepSeek API，开启 JSON Output。
4. 加上本地 SQLite 记忆写入。
5. 做演示视频与评测截图。

## 版权与作品集说明

本包中的角色资料是公开资料的摘要化改写，用于技术作品集 demo。不要复制官方长台词、图片、语音或模型资产。对外展示时建议明确说明：本项目展示 RAG NPC Agent 工程能力，角色 IP 归原权利方所有。
