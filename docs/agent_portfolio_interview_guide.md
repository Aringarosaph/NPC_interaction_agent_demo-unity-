# NPC Agent Demo 面试说明

本文档用于帮助面试官快速理解本项目的目标、可运行路径、关键实现和技术取舍。

## 30 秒简介

这是一个 Unity + FastAPI 的游戏 NPC Agent demo。玩家在 Unity 场景中靠近阿米娅、八重神子或今汐后输入文字，Unity 将请求发送给本地 FastAPI 后端。后端结合角色资料、RAG 检索、SQLite 长期记忆、任务/关系/背包状态、planner 和受控工具调用生成短回复，并把 trace/world events 返回给 Unity。Unity 端显示 NPC 气泡，同时右上角调试面板展示 agent 状态变化。

项目重点不是“让模型自由发挥”，而是展示一个游戏项目中更可控的 Agent loop：

```text
Unity input
-> backend v2 dialogue
-> retrieve + memory + state
-> planner
-> validated tools
-> short utterances
-> self-check
-> Unity bubbles + debug panel
```

## 运行入口

后端：

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8008
```

Unity：

```text
unity/PortfolioNpcRagWhitebox
Assets/Scenes/Scene_PortfolioNpcRag.unity
```

行为评测：

```bash
backend/.venv/bin/python eval/run_eval.py \
  --backend http://127.0.0.1:8008 \
  --out eval/reports/latest_report.md \
  --json-out eval/reports/latest_report.json
```

## 主要看点

| 看点 | 位置 |
| --- | --- |
| v2 Agent 编排 | `backend/app/orchestrator.py` |
| Planner | `backend/app/agent_planner.py` |
| 工具注册与校验 | `backend/app/tools/` |
| 世界状态持久化 | `backend/app/state_store.py` |
| 长期记忆与策略 | `backend/app/memory_store.py`, `backend/app/memory_policy.py` |
| 自检与 reflection | `backend/app/self_check.py` |
| Unity v2 client | `unity/PortfolioNpcRagWhitebox/Assets/Scripts/NpcDialogue/NpcDialogueClient.cs` |
| Unity debug panel | `unity/PortfolioNpcRagWhitebox/Assets/Scripts/NpcDialogue/AgentDebugPanelController.cs` |
| 行为评测 | `eval/run_eval.py`, `eval/cases/`, `eval/reports/latest_report.md` |

## 技术取舍

- 使用 FastAPI + Pydantic 保持接口清晰，Unity 只消费稳定 JSON，不直接接触 LLM key。
- 使用本地 YAML/SQLite，降低部署复杂度，同时保留真实项目里的 profile、memory、state、event 边界。
- 使用确定性 planner 作为当前 demo 的默认路径，保证可测、可复现；未来可以替换为受限 JSON planner。
- 工具调用必须经过后端注册表和参数校验，避免模型自由改写任务/物品/关系状态。
- v1 接口保留，v2 接口新增 trace/world events，方便渐进升级和兼容旧 Unity 客户端。

## 最新验证

截至当前提交：

- 后端 pytest：41 tests + 3 subtests passed。
- 后端 unittest：37 tests passed。
- Eval：11/11 cases passed，覆盖 persona、boundary、retrieval、tool use、world event、memory、format、quest flow。
- Unity validator：场景、v2 endpoint、NPC markers、中文字体、debug panel 引用校验通过。
- Unity Play Mode smoke：能连接本地 `/api/v2/dialogue` 完成实机对话请求。

## 可讨论的后续扩展

- 将 `emotion/action` 接入角色动画状态机。
- 将确定性 planner 扩展为受限 JSON planner，并继续由后端校验工具调用。
- 扩大知识库与 quest flow，增加多 NPC 公共事件订阅。
- 把 eval runner 接入 CI，形成每次提交的行为回归门禁。
