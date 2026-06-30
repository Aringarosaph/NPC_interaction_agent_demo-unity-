# Phase 00 - 项目初始化

目标：把本包整理成一个可运行仓库。

任务：
1. 在仓库根目录保留 `data/`, `schemas/`, `prompts/`, `config/`。
2. 将 `backend_scaffold/` 改名或复制为 `backend/`。
3. 将 `unity_scaffold/Assets/Scripts/NpcDialogue/` 复制到 Unity 项目的 `Assets/Scripts/NpcDialogue/`。
4. 确认 Python 虚拟环境和 requirements 安装成功。
5. 跑通 `GET /api/v1/health`。

验收：
- `python -m app.main` 能启动。
- 浏览器访问 `http://127.0.0.1:8008/api/v1/health` 返回 ok。


通用约束：
- 不改 `schemas/` 中已冻结字段名。
- 不把 Unity 客户端直接连 DeepSeek；必须通过本地 FastAPI。
- NPC 回复必须是 1-3 句短气泡，不允许长段落。
- 角色不知道其他作品世界、Unity、AI、后端。
- 先保证可跑，再优化表现。
