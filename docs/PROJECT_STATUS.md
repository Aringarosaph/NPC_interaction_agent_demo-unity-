# NPC RAG Agent 项目状态

## 项目定位

本项目是一套用于求职展示的 Unity + FastAPI NPC Agent Demo。玩家可在 Unity 场景中接近阿米娅、八重神子和今汐并进行自然语言对话；本地后端通过 RAG、长期记忆、任务与世界状态、受约束工具和回复自检生成可追踪的结构化响应。

项目以一套完整成品对外呈现，不使用版本迁移式口径。角色名称、设定与展示模型仅用于非商用作品集。

## 当前环境

- 远端仓库：`https://github.com/Aringarosaph/NPC_interaction_agent_demo-unity-`
- 主分支：`main`
- Unity：`6000.4.2f1`，Unity Personal 许可证已通过批处理运行验证。
- Python：`/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14`
- GitHub CLI：`/opt/homebrew/bin/gh`
- Git LFS：`git-lfs/3.7.1`

## 已完成功能

- [x] 初始化 Git 并连接公开 GitHub 仓库。
- [x] 搭建 FastAPI 后端，接入 DeepSeek JSON 输出、RAG 检索与 SQLite 记忆。
- [x] 实现包含规划、受约束工具、世界状态、世界事件与执行追踪的 Agent Loop。
- [x] 实现实用型记忆策略、回复自检和行为评测脚本。
- [x] Unity 接入统一对话接口、NPC 距离检测、输入框、姓名牌、自适应气泡和调试面板。
- [x] 将现有美术场景和三名 NPC 模型接入完整对话链路。
- [x] 调试面板支持重置本地记忆、任务、关系、背包和世界事件，便于反复演示。
- [x] 八重神子支持六种受约束表情和六种站立动作，并提供 `neutral` / `idle` 回退。
- [x] 玩家角色替换为安比模型，支持武器骨骼、Idle/Walk 动画和停止移动时立即退出 Walk。
- [x] 支持第一、第三人称视角切换，以及第三人称滚轮和 macOS 触控板缩放。
- [x] README 和面试说明已整理为面向面试官的中文成品文档。

## 对外接口

- `GET /api/health`
- `POST /api/dialogue`
- `GET /api/debug/retrieve`
- `GET /api/debug/memories`
- `POST /api/debug/reset`

Unity 运行时的 NPC 对话统一调用 `POST /api/dialogue`；其他接口用于健康检查、检索与记忆调试，以及演示状态重置。

## 维护约束

- 未经明确确认，不修改 `schemas/` 中已经稳定的数据契约。
- Unity 只通过本地 FastAPI 访问模型，不直接调用 DeepSeek。
- NPC 回复保持为 1-3 条短句，并继续执行跨世界、AI、Unity、后端和系统提示词边界处理。
- 对外角色表现字段限制在公开的 `expression` 与 `action` 枚举内；Unity 资源名称只作为内部映射细节。
- `.env`、本地 SQLite 状态、虚拟环境、Unity 生成目录、派生记忆和未使用美术资源不进入版本库。
- 有意纳入版本管理的大型 Unity 美术资源继续使用 Git LFS。
- 每次阶段目标、范围或验证结果发生实质变化时更新本文档。

## 本地环境提示

- PATH 中的 `python3` 可能仍指向 macOS 系统 Python；必要时直接使用上方 Python 3.14 完整路径。
- 若 `gh auth status` 报告凭据失效，但 Git 凭据仍可能允许正常推送；无法推送时执行 `gh auth login -h github.com` 重新登录。

## 最近验证记录

### 2026-07-07：后端与 Unity 主链路

- `cd backend && .venv/bin/python -m pytest -q`：40 项测试及 3 项子测试通过。
- `cd backend && .venv/bin/python -m unittest discover -s tests`：36 项测试通过；仅存在进程级 SQLite Store 引发的已知非致命 `ResourceWarning`。
- Python 编译检查、Unity 美术场景绑定和白盒场景验证通过。
- 行为评测 11/11 用例通过，共 13 轮对话，总体通过率 100%。
- Unity Play Mode 成功调用 `POST /api/dialogue`，后端对话冒烟测试通过。

### 2026-07-08：演示状态重置

- `POST /api/debug/reset?player_id=local_player` 可清除运行时记忆与状态，同时保留种子记忆。
- Pytest 42 项测试及 3 项子测试通过；unittest 38 项测试通过。
- Unity 场景绑定、场景验证、对话与重置 Play Mode 冒烟测试全部通过。

### 2026-07-14：角色表现与玩家控制

- 后端回复契约统一为六值 `expression` 与六值 `action`，每次回复最多播放一个非 Idle 动作。
- Pytest 43 项测试及 3 项子测试通过；unittest 39 项测试通过。
- 八重神子六套表情预设、六个 Animator 状态和所需 Shape Key 均验证通过。
- Unity Play Mode 成功应用 `teasing` 表情并进入 `nod` 动作状态；真实模型对话也返回并播放了结构化表情和动作。
- 安比 Idle/Walk 切换、脚部落地、武器骨骼、第一/第三人称切换和第三人称缩放均通过 Play Mode 验证。

## 当前状态

后端、Unity 对话主链路、记忆与任务状态、八重神子角色表现、安比玩家控制和双视角相机均已形成可运行闭环。后续工作应围绕演示稳定性、内容质量和必要的体验打磨展开，避免无明确收益的架构扩张。
