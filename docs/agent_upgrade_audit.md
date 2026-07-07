# Agent System Audit

> Created: 2026-07-07
> Updated: 2026-07-07
> Purpose: record the current repo structure after the NPC agent loop upgrade.

## 1. Backend Entry Points

- `backend/app/main.py`
  - Creates the FastAPI app.
  - Exposes `GET /api/health`.
  - Exposes `POST /api/dialogue`.
  - Exposes `GET /api/debug/retrieve`.
  - Exposes `GET /api/debug/memories`.
  - Instantiates a process-level `DialogueOrchestrator`.

- `backend/app/config.py`
  - Loads `.env`.
  - Reads `config/demo_config.yaml`.
  - Defines data/config roots, DeepSeek settings, host, port, and mock behavior.

## 2. Backend Agent Flow

- `backend/app/orchestrator.py`
  - Main class: `DialogueOrchestrator`.
  - Public production method: `handle(req: DialogueRequest) -> AgentDialogueResponse`.
  - Internal normalization path: `ResponseNormalizer` produces a compact normalized response used by self-check and trace assembly.

Current flow:

```text
load NPC bundle
-> range guard
-> retrieve knowledge chunks
-> retrieve memories
-> read state snapshot
-> plan backend tool calls
-> execute validated tools
-> build prompt with state, plan, and tool results
-> call LLM or mock fallback
-> deterministic preferred-address memory extraction
-> trust-filter used ids
-> normalize response
-> run self-check and fallback repair if needed
-> write accepted memory candidates
-> return dialogue_response.agent
```

- `backend/app/agent_planner.py`
  - Plans deterministic tool calls for lightweight quest acceptance/completion and relationship updates.

- `backend/app/tools/`
  - Holds registered backend tool specs, validation, execution context, and game-state tool implementations.
  - Unity and LLM output never mutate state directly.

- `backend/app/state_store.py`
  - SQLite-backed player state, relationships, quest states, inventory items, and world events.

- `backend/app/self_check.py`
  - Checks response format and safety constraints before the final response leaves the backend.

## 3. RAG, Prompting, and Generation

- `backend/app/data_loader.py`
  - Loads NPC data from `data/npcs/index.yaml`.
  - Per NPC files:
    - `profile.yaml`
    - `knowledge_chunks.yaml`
    - `dialogue_examples.yaml`
    - `memory_seed.yaml`

- `backend/app/retriever.py`
  - Uses `TfidfVectorizer` with character n-grams.
  - Applies visibility filters for NPC id, quest stage, and spoiler level.
  - Handles cross-world/meta boundary chunks.

- `backend/app/prompt_builder.py`
  - Builds system/user messages for profile, world state, memory, retrieved knowledge, and player input.
  - Enforces short JSON output requirements in the prompt.

- `backend/app/llm_client.py`
  - Uses OpenAI-compatible `AsyncOpenAI` against DeepSeek.
  - Requests JSON mode and disables thinking through `extra_body`.
  - Falls back to deterministic mock output if mock mode is active or an exception happens.

## 4. Memory

- `backend/app/memory_store.py`
  - SQLite-backed store at `backend/local_memory.sqlite` by default.
  - Supports seed upsert, keyword/salience search, debug listing, and write candidate persistence.

- `backend/app/memory_policy.py`
  - Allows practical memory types: `preference`, `promise`, `event`, `relationship`, `reflection`, `fact`.
  - Validates summary/detail/salience and filters sensitive implementation leakage.
  - Supersedes older active preferred-address records when the player gives a new preferred name.

## 5. Models and Schemas

- `backend/app/models.py`
  - Request and world state:
    - `WorldState`
    - `DialogueRequest`
  - Utterances and internal normalization:
    - `Utterance`
    - `InternalDebug`
    - `NormalizedDialogueResponse`
  - Agent response:
    - `AgentPlan`
    - `ToolCall`
    - `ToolResult`
    - `WorldEvent`
    - `AgentTrace`
    - `AgentDialogueResponse`
  - Debug output:
    - `RetrievedChunk`
    - `DebugRetrieveResponse`
    - `MemorySnippet`
    - `MemoryDebugRecord`
    - `DebugMemoriesResponse`

- `schemas/`
  - `dialogue_request.schema.json`
  - `dialogue_response.schema.json`
  - `dialogue_response.agent.example.json`
  - `agent_trace.example.json`
  - `knowledge_chunk.schema.json`
  - `memory_record.schema.json`
  - `npc_profile.schema.json`

## 6. Unity Client and Scene Integration

- Unity project root:
  - `unity/PortfolioNpcRagWhitebox`

- Main scene:
  - `unity/PortfolioNpcRagWhitebox/Assets/Scenes/Scene_PortfolioNpcRag.unity`

- Runtime dialogue scripts:
  - `Assets/Scripts/NpcDialogue/NpcModels.cs`
    - Contains request and agent response DTOs.
  - `Assets/Scripts/NpcDialogue/NpcDialogueClient.cs`
    - Sends `DialogueRequestDto` to `http://127.0.0.1:8008/api/dialogue`.
    - Parses `DialogueResponseDto`.
    - Displays NPC utterances and agent debug state.
  - `Assets/Scripts/NpcDialogue/PlayerChatInput.cs`
    - Handles Enter/Escape input focus and send action.
  - `Assets/Scripts/NpcDialogue/DialogueRangeDetector.cs`
    - Tracks nearest active NPC by `NpcAgentMarker`.
  - `Assets/Scripts/NpcDialogue/NpcAgentMarker.cs`
    - Stores NPC id, display name, range center, interaction radius, and bubble anchor.
  - `Assets/Scripts/NpcDialogue/SpeechBubbleController.cs`
    - Displays world/player bubble text.
  - `Assets/Scripts/NpcDialogue/AgentDebugPanelController.cs`
    - Displays world events, trace, tool calls/results, and self-check details.

- Player/camera scripts:
  - `Assets/Scripts/Whitebox/WhiteboxPlayerController.cs`
  - `Assets/Scripts/Whitebox/SimpleThirdPersonCamera.cs`
  - `Assets/Scripts/Whitebox/BillboardToCamera.cs`

- Editor automation:
  - `Assets/Editor/WhiteboxSceneBuilder.cs`
    - Builds and validates the scene.
  - `Assets/Editor/ArtSceneDialogueBinder.cs`
    - Rebinds current art scene NPC meshes to dialogue markers, nameplates, bubbles, colliders, and debug UI.
  - `Assets/Editor/BackendDialoguePlayModeSmoke.cs`
    - Runs Unity Play Mode backend smoke.
  - `Assets/Scripts/NpcDialogue/BackendDialoguePlayModeSmokeRunner.cs`
    - Sends a real Unity client request during Play Mode smoke.

## 7. Current Capabilities

- Unity playable scene with:
  - third-person camera
  - WASD/arrow movement
  - Enter-focused input field
  - current art scene and three character meshes
  - NPC nameplates
  - world-space player/NPC speech bubbles
  - interaction range detection based on current art mesh roots
  - agent debug panel

- Backend:
  - FastAPI app
  - unified dialogue endpoint
  - debug retrieval endpoint
  - debug memory endpoint
  - DeepSeek JSON mode integration
  - mock fallback when no API key or LLM call fails
  - response normalization and self-check

- Agent behavior:
  - per-NPC RAG
  - SQLite memory
  - SQLite world state
  - deterministic planner
  - validated backend tools
  - traceable world events
  - behavior evaluation reports

## 8. Validation Commands

Backend unit/regression tests:

```bash
cd backend
source .venv/bin/activate
python -m pytest -q
python -m unittest discover -s tests
```

Backend health check with server running:

```bash
curl http://127.0.0.1:8008/api/health
```

Unity scene validation:

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

## 9. Maintenance Rules

- Keep `POST /api/dialogue` as the single public Unity dialogue endpoint.
- Keep the agent response shape stable for Unity:
  - `schema_version`
  - `turn_id`
  - `npc_id`
  - `utterances`
  - `world_events`
  - `trace`
- Keep `Utterance` fields stable:
  - `text`
  - `emotion`
  - `action`
  - `delay_ms`
- Existing NPC ids must remain valid:
  - `arknights_amiya`
  - `genshin_yae_miko`
  - `wuwa_jinhsi`
- Keep debug endpoints stable:
  - `/api/debug/retrieve`
  - `/api/debug/memories`
- `.env`, local SQLite runtime files, Unity generated folders, and unused imported art should stay out of commits.
