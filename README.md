# Unity NPC RAG Agent 作品集 Demo

这是一个可运行的 Unity + FastAPI NPC 交互作品集 demo。项目展示了如何把角色资料、知识检索、本地记忆、LLM JSON 输出和 Unity 气泡对话串成一条完整、可验证的交互链路。

当前白盒场景包含一名玩家和三名 NPC：阿米娅、八重神子、今汐。玩家靠近 NPC 后输入文字，Unity 会把请求发送到本地 FastAPI 后端；后端根据 NPC 资料、RAG 检索结果和本地记忆生成 1-3 句短回复，再由 Unity 逐句显示在 NPC 头顶气泡中。

## 项目亮点

- **Unity 可运行白盒**：包含地板、玩家胶囊、三个 NPC 胶囊、第三视角鼠标视角、WASD 移动、中文名字牌、玩家/NPC 气泡和输入框。
- **本地 FastAPI 后端**：Unity 只连接本地后端，不直接暴露或调用 LLM API。
- **RAG 角色知识检索**：每个 NPC 都有独立的 profile、knowledge chunks、dialogue examples 和 memory seed。
- **可控 JSON 输出**：后端把模型回复归一化为 `utterances`，字段包括 `text`、`emotion`、`action`、`delay_ms`，方便 Unity 稳定消费。
- **本地 SQLite 记忆**：支持写入和召回玩家偏好，例如“以后叫我小吴”。
- **角色边界处理**：角色不会假装知道其他作品世界、Unity、AI、后端等出戏内容。
- **自动化验证**：已包含后端测试、Unity 场景 validator、Unity Play Mode backend smoke。

## 快速开始

### 0. 首次准备后端环境

如果是第一次 clone 项目，先准备后端虚拟环境：

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

如果希望使用真实 LLM 输出，在 `backend/.env` 中填写：

```text
DEEPSEEK_API_KEY=你的 key
```

如果没有配置 key，后端也可以按配置使用 mock 输出，便于本地开发和演示基础链路。

### 1. 启动后端

在仓库根目录执行：

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8008
```

看到类似以下内容，就说明后端已经启动：

```text
Uvicorn running on http://127.0.0.1:8008
```

可以在另一个终端检查健康状态：

```bash
curl http://127.0.0.1:8008/api/v1/health
```

预期响应：

```json
{"ok":true,"service":"portfolio-npc-rag-agent"}
```

### 2. 打开 Unity 项目

使用 Unity 打开，项目版本为 `6000.4.2f1`：

```text
unity/PortfolioNpcRagWhitebox
```

打开场景：

```text
Assets/Scenes/Scene_PortfolioNpcRag.unity
```

如果需要重新生成白盒场景，执行：

```text
NPC Demo > Build Whitebox Scene
```

### 3. 进入 Play Mode

在 Unity Play Mode 中：

- 使用 `WASD` 或方向键移动。
- 使用鼠标控制视角。
- 靠近 NPC，直到底部当前 NPC 标签变化。
- 按 `Enter` 聚焦输入框。
- 输入文本后按 `Enter` 或点击 `发送`。
- 按 `Esc` 退出输入模式，恢复移动和鼠标视角。

## 本地后端开关

启动后端：

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8008
```

关闭后端：

- 在运行 uvicorn 的终端按 `Ctrl+C`。
- 如果不确定后端是否还在运行，可以检查 8008 端口：

```bash
lsof -nP -iTCP:8008 -sTCP:LISTEN
```

如果仍有进程监听，并且你确认要手动停止它：

```bash
kill <PID>
```

把 `<PID>` 替换为 `lsof` 输出里的进程 id。

## 可直接使用的短提示词例子（demo知识库体量有限，仅涵盖一部分核心信息）

```text
阿米娅，罗德岛的使命是什么？
源石病是什么？
我想给八重堂投稿。
今汐，我有一个愿望。
以后叫我小吴。
你记得怎么叫我吗？
```

## API 示例

```bash
curl -X POST http://127.0.0.1:8008/api/v1/dialogue \
  -H "Content-Type: application/json" \
  -d '{"schema_version":"dialogue_request.v1","session_id":"demo","player_id":"local_player","npc_id":"arknights_amiya","player_text":"阿米娅，罗德岛的使命是什么？","distance_m":1.5,"is_in_range":true,"world_state":{"location_id":"portfolio_whitebox_room","game_time_label":"demo","quest_stage":0,"relationship_score":0,"debug_enabled":true}}'
```

后端会返回 Unity 稳定消费的结构：

```json
{
  "schema_version": "dialogue_response.v1",
  "turn_id": "turn_xxx",
  "npc_id": "arknights_amiya",
  "utterances": [
    {
      "text": "当然记得，博士。",
      "emotion": "gentle",
      "action": "nod",
      "delay_ms": 500
    }
  ],
  "internal": {
    "used_knowledge_ids": ["amiya_rhodes_mission"],
    "used_memory_ids": [],
    "memory_candidates": [],
    "confidence": 0.9
  }
}
```

预留了情绪与动作字段，后期可接入游戏。

## 验证方式

后端测试：

```bash
cd backend
source .venv/bin/activate
python -m pytest -q
python -m unittest discover -s tests
```

Unity 场景校验，在仓库根目录执行：

```bash
"/Applications/Unity/Hub/Editor/6000.4.2f1/Unity.app/Contents/MacOS/Unity" \
  -batchmode \
  -projectPath "unity/PortfolioNpcRagWhitebox" \
  -executeMethod WhiteboxSceneBuilder.ValidateWhiteboxScene \
  -quit \
  -logFile -
```

后端已启动时，可以运行 Unity Play Mode 联调 smoke：

```bash
"/Applications/Unity/Hub/Editor/6000.4.2f1/Unity.app/Contents/MacOS/Unity" \
  -batchmode \
  -projectPath "unity/PortfolioNpcRagWhitebox" \
  -executeMethod BackendDialoguePlayModeSmoke.Run \
  -logFile /tmp/npc_unity_playmode_backend_smoke.log
```

预期成功标记：

```text
Unity backend Play Mode smoke passed.
```

## 目录结构

- `backend/`：FastAPI 服务、RAG 编排、LLM client、本地记忆和测试。
- `unity/PortfolioNpcRagWhitebox/`：Unity 6000.4.2f1 白盒项目。
- `data/npcs/`：三名 NPC 的 profile、knowledge、examples、memory seed。
- `schemas/`：Unity 与后端共用的数据契约。
- `prompts/`：系统提示词、上下文模板、记忆提取模板。
- `docs/`：架构、后端、Unity、prompt、评测和版权说明。
- `eval/`：角色、知识边界、短句输出、记忆测试用例。
- `codex_tasks/`：分阶段开发任务记录。

## 本地配置

真实 DeepSeek 输出需要在 `backend/.env` 中设置 `DEEPSEEK_API_KEY`。该文件已被 git 忽略，不会提交到公开仓库。

如果没有配置 key，后端可以根据 `MOCK_LLM_WHEN_NO_KEY` 使用 mock 输出，方便本地开发。

当前开发验证过的本地环境：

- Python `3.14.6`
- Unity `6000.4.2f1`
- 后端地址 `http://127.0.0.1:8008`

## 作品集与版权说明

本仓库中的角色资料是为非商用技术作品集 demo 做的摘要化、改写化整理。项目不包含官方图片、语音、模型或大段复制台词。角色 IP 归原权利方所有。

## License

项目代码和文档使用 MIT License，见 `LICENSE`。

随仓库附带的第三方资源保留其原有许可证，见 `THIRD_PARTY_NOTICES.md`。
