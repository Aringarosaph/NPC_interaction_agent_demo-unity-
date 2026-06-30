# Portfolio NPC RAG Agent Demo

一个可运行的 Unity + FastAPI NPC 交互作品集 demo。项目演示了如何把角色资料、知识检索、短期/长期记忆、LLM JSON 输出和 Unity 气泡对话串成一条可验证链路。

当前白盒场景包含一名玩家和三名 NPC：阿米娅、八重神子、今汐。玩家靠近 NPC 后输入文本，Unity 会把请求发送到本地 FastAPI 后端；后端根据 NPC 资料、RAG 检索结果和本地记忆生成 1-3 句短回复，再由 Unity 逐句显示在 NPC 头顶气泡中。

## Project Highlights

- **Unity 可运行白盒**：地板、玩家胶囊、三个 NPC 胶囊、第三视角鼠标视角、WASD 移动、中文名字牌、玩家/NPC 气泡和输入框。
- **本地 FastAPI 后端**：统一承接 Unity 请求，避免 Unity 直接暴露或调用 LLM API。
- **RAG 角色知识检索**：每个 NPC 拥有 profile、knowledge chunks、dialogue examples 和 memory seed。
- **可控 JSON 输出**：LLM 回复归一化为 `utterances`，包含 `text`、`emotion`、`action`、`delay_ms`。
- **本地 SQLite 记忆**：支持写入和召回玩家偏好，例如“以后叫我小林”。
- **边界处理**：角色不会假装知道其他作品世界、Unity、AI、后端等出戏内容。
- **自动化验证**：后端测试、Unity 场景 validator、Unity Play Mode backend smoke 均已落地。
- **公开仓库安全**：`.env`、本地记忆数据库、虚拟环境、Unity `Library/` 和派生缓存均被忽略。

## Quick Start

### 0. First-time Backend Setup

If this is a fresh clone, prepare the backend environment first:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

For real LLM output, put `DEEPSEEK_API_KEY=...` in `backend/.env`. Without a key, the backend can use mock output for local development.

### 1. Start Backend

From the repository root:

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8008
```

Expected output includes:

```text
Uvicorn running on http://127.0.0.1:8008
```

Health check in another terminal:

```bash
curl http://127.0.0.1:8008/api/v1/health
```

Expected response:

```json
{"ok":true,"service":"portfolio-npc-rag-agent"}
```

### 2. Open Unity Project

Open this folder with Unity `6000.4.2f1`:

```text
unity/PortfolioNpcRagWhitebox
```

Open or rebuild the scene:

```text
Assets/Scenes/Scene_PortfolioNpcRag.unity
```

If the scene needs to be regenerated:

```text
NPC Demo > Build Whitebox Scene
```

### 3. Play

In Unity Play Mode:

- Move with `WASD` or arrow keys.
- Look around with the mouse.
- Approach an NPC until the current NPC label changes.
- Press `Enter` to focus the input field.
- Type a message, then press `Enter` or click `发送`.
- Press `Esc` to leave typing mode and return to camera control.

## Backend On/Off

Start backend:

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8008
```

Stop backend:

- In the terminal running uvicorn, press `Ctrl+C`.
- If you are unsure whether it is still running:

```bash
lsof -nP -iTCP:8008 -sTCP:LISTEN
```

If a process is still listening and you want to stop it manually:

```bash
kill <PID>
```

Replace `<PID>` with the process id shown by `lsof`.

## Demo Recording Flow

1. Start the backend and leave that terminal open.
2. Open `unity/PortfolioNpcRagWhitebox` in Unity.
3. Open `Assets/Scenes/Scene_PortfolioNpcRag.unity`.
4. Enter Play Mode.
5. Walk to 阿米娅 and ask about 罗德岛 or 源石病.
6. Walk to 八重神子 and ask about 投稿 or 轻小说.
7. Walk to 今汐 and ask about 愿望 or 今州.
8. Optional memory demo: tell one NPC `以后叫我小林`, then ask `你记得怎么叫我吗？`.

Good short prompts:

```text
阿米娅，罗德岛的使命是什么？
源石病是什么？
我想给八重堂投稿。
今汐，我有一个愿望。
以后叫我小林。
你记得怎么叫我吗？
```

## API Example

```bash
curl -X POST http://127.0.0.1:8008/api/v1/dialogue \
  -H "Content-Type: application/json" \
  -d '{"schema_version":"dialogue_request.v1","session_id":"demo","player_id":"local_player","npc_id":"arknights_amiya","player_text":"阿米娅，罗德岛的使命是什么？","distance_m":1.5,"is_in_range":true,"world_state":{"location_id":"portfolio_whitebox_room","game_time_label":"demo","quest_stage":0,"relationship_score":0,"debug_enabled":true}}'
```

The response shape is stable for Unity:

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

## Validation

Backend tests:

```bash
cd backend
source .venv/bin/activate
python -m pytest -q
python -m unittest discover -s tests
```

Unity scene validation from repository root:

```bash
"/Applications/Unity/Hub/Editor/6000.4.2f1/Unity.app/Contents/MacOS/Unity" \
  -batchmode \
  -projectPath "unity/PortfolioNpcRagWhitebox" \
  -executeMethod WhiteboxSceneBuilder.ValidateWhiteboxScene \
  -quit \
  -logFile -
```

Unity Play Mode backend smoke, with backend already running:

```bash
"/Applications/Unity/Hub/Editor/6000.4.2f1/Unity.app/Contents/MacOS/Unity" \
  -batchmode \
  -projectPath "unity/PortfolioNpcRagWhitebox" \
  -executeMethod BackendDialoguePlayModeSmoke.Run \
  -logFile /tmp/npc_unity_playmode_backend_smoke.log
```

Expected success marker:

```text
Unity backend Play Mode smoke passed.
```

## Repository Layout

- `backend/`：FastAPI 服务、RAG 编排、LLM client、本地记忆、测试。
- `unity/PortfolioNpcRagWhitebox/`：Unity 6000.4.2f1 白盒项目。
- `data/npcs/`：三名 NPC 的 profile、knowledge、examples、memory seed。
- `schemas/`：Unity 与后端共用的数据契约。
- `prompts/`：系统提示词、上下文模板、记忆提取模板。
- `docs/`：架构、后端、Unity、prompt、评测和版权说明。
- `eval/`：角色、知识边界、短句输出、记忆测试用例。
- `codex_tasks/`：分阶段开发任务记录。

## Local Configuration

For real DeepSeek output, set `DEEPSEEK_API_KEY` in `backend/.env`. This file is ignored by git.

If no key is configured, the backend can fall back to mock output for local development according to `MOCK_LLM_WHEN_NO_KEY`.

The verified local runtime used during development:

- Python `3.14.6`
- Unity `6000.4.2f1`
- Backend URL `http://127.0.0.1:8008`

## Portfolio And Copyright Note

The character material in this repository is summarized and rewritten for a non-commercial technical portfolio demo. The project does not include official images, voice, models, or long copied dialogue. Character IP belongs to the original rights holders.

## License

Project code and documentation are released under the MIT License. See `LICENSE`.

Bundled third-party assets keep their own licenses. See `THIRD_PARTY_NOTICES.md`.
