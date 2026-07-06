# Agent Upgrade Baseline Audit

> Created: 2026-07-07
> Purpose: record the current repo baseline before adding the v2 game NPC agent loop.

## 1. Current Structure

### Backend Entry Points

- `backend/app/main.py`
  - Creates the FastAPI app.
  - Exposes `GET /api/v1/health`.
  - Exposes `POST /api/v1/dialogue`.
  - Exposes `GET /api/v1/debug/retrieve`.
  - Exposes `GET /api/v1/debug/memories`.
  - Instantiates a process-level `DialogueOrchestrator`.

- `backend/app/config.py`
  - Loads `.env`.
  - Reads `config/demo_config.yaml`.
  - Defines data/config roots, DeepSeek settings, host, port, and mock behavior.

### Backend Orchestration and Generation

- `backend/app/orchestrator.py`
  - Current main class: `DialogueOrchestrator`.
  - Current production method: `handle(req: DialogueRequest) -> DialogueResponse`.
  - Current flow:

    ```text
    load npc bundle
    -> range guard
    -> retrieve knowledge chunks
    -> retrieve memories
    -> build prompt
    -> call LLM or mock fallback
    -> deterministic preferred-address memory extraction
    -> trust-filter used ids
    -> normalize response
    -> write memory candidates
    -> return dialogue_response.v1
    ```

- `backend/app/prompt_builder.py`
  - Builds system/user messages for profile, world state, memory, retrieved knowledge, and player input.
  - Enforces short 1-3 utterance JSON output in the prompt.

- `backend/app/llm_client.py`
  - Uses OpenAI-compatible `AsyncOpenAI` against DeepSeek.
  - Requests JSON mode and disables thinking through `extra_body`.
  - Falls back to deterministic mock output if mock mode is active or an exception happens.

- `backend/app/response_normalizer.py`
  - Converts raw model JSON into `DialogueResponse`.
  - Clamps emotions/actions to allowlists.
  - Enforces max utterance count and sentence length.
  - Provides a safe fallback utterance when output is empty.

### Data Loading and Retrieval

- `backend/app/data_loader.py`
  - Loads NPC data from `data/npcs/index.yaml`.
  - Per NPC files:
    - `profile.yaml`
    - `knowledge_chunks.yaml`
    - `dialogue_examples.yaml`
    - `memory_seed.yaml`

- `backend/app/retriever.py`
  - Current retriever: `SmallKnowledgeRetriever`.
  - Uses `TfidfVectorizer` with character n-grams.
  - Applies visibility filters for NPC id, quest stage, and spoiler level.
  - Has hard boundary keyword handling for cross-world/meta questions.

- Current NPC data packs:
  - `data/npcs/arknights_amiya/`
  - `data/npcs/genshin_yae_miko/`
  - `data/npcs/wuwa_jinhsi/`

### Memory Store

- `backend/app/memory_store.py`
  - SQLite-backed store at `backend/local_memory.sqlite` by default.
  - Table: `memories`.
  - Supports seed upsert, keyword/salience search, debug listing, and write candidate persistence.
  - Current accepted write types: `promise`, `preference`, `relationship`, `event`, `fact`.
  - Current behavior does not yet handle preferred-address superseding or reflection memories.

### Models and Schemas

- `backend/app/models.py`
  - Current v1 API models:
    - `WorldState`
    - `DialogueRequest`
    - `Utterance`
    - `InternalDebug`
    - `DialogueResponse`
    - `RetrievedChunk`
    - `DebugRetrieveResponse`
    - `MemorySnippet`
    - `MemoryDebugRecord`
    - `DebugMemoriesResponse`

- `schemas/`
  - `dialogue_request.schema.json`
  - `dialogue_response.schema.json`
  - `knowledge_chunk.schema.json`
  - `memory_record.schema.json`
  - `npc_profile.schema.json`

### Unity Client and Scene Integration

- Unity project root:
  - `unity/PortfolioNpcRagWhitebox`

- Main scene:
  - `unity/PortfolioNpcRagWhitebox/Assets/Scenes/Scene_PortfolioNpcRag.unity`

- Runtime dialogue scripts:
  - `Assets/Scripts/NpcDialogue/NpcModels.cs`
    - Contains current v1 DTOs.
  - `Assets/Scripts/NpcDialogue/NpcDialogueClient.cs`
    - Sends `DialogueRequestDto` to `http://127.0.0.1:8008/api/v1/dialogue`.
    - Parses `DialogueResponseDto`.
    - Displays NPC utterances in world-space bubbles.
  - `Assets/Scripts/NpcDialogue/PlayerChatInput.cs`
    - Handles Enter/Escape input focus and send action.
  - `Assets/Scripts/NpcDialogue/DialogueRangeDetector.cs`
    - Tracks nearest active NPC by `NpcAgentMarker`.
  - `Assets/Scripts/NpcDialogue/NpcAgentMarker.cs`
    - Stores NPC id, display name, range center, interaction radius, and bubble anchor.
  - `Assets/Scripts/NpcDialogue/SpeechBubbleController.cs`
    - Displays world/player bubble text.

- Player/camera scripts:
  - `Assets/Scripts/Whitebox/WhiteboxPlayerController.cs`
  - `Assets/Scripts/Whitebox/SimpleThirdPersonCamera.cs`
  - `Assets/Scripts/Whitebox/BillboardToCamera.cs`

- Editor automation:
  - `Assets/Editor/WhiteboxSceneBuilder.cs`
    - Builds and validates the scene.
  - `Assets/Editor/ArtSceneDialogueBinder.cs`
    - Rebinds current art scene NPC meshes to dialogue markers, nameplates, bubbles, and colliders.
  - `Assets/Editor/BackendDialoguePlayModeSmoke.cs`
    - Runs Unity Play Mode backend smoke.
  - `Assets/Scripts/NpcDialogue/BackendDialoguePlayModeSmokeRunner.cs`
    - Sends a real Unity client request during Play Mode smoke.

## 2. Existing Capabilities

- Unity playable scene with:
  - third-person camera
  - WASD/arrow movement
  - Enter-focused input field
  - current art scene and three character meshes
  - NPC nameplates
  - world-space player/NPC speech bubbles
  - interaction range detection based on current art mesh roots

- Backend:
  - FastAPI app
  - v1 health endpoint
  - v1 dialogue endpoint
  - debug retrieval endpoint
  - debug memory endpoint
  - DeepSeek JSON mode integration
  - mock fallback when no API key or LLM call fails
  - response normalization

- RAG:
  - per-NPC knowledge chunks
  - character n-gram TF-IDF retrieval
  - quest stage/spoiler visibility filters
  - boundary handling for cross-world/meta questions

- Memory:
  - SQLite persistence
  - seed memories from data packs
  - explicit preferred-address extraction, such as `以后叫我小林`
  - memory recall by keyword/salience

- Tests and validation:
  - Python pytest/unittest coverage for mock dialogue, retrieval, LLM client, memory, and normalization.
  - Unity editor scene validator.
  - Unity Play Mode backend smoke.

## 3. Current Gaps for the Agent Upgrade

- No v2 response schema for agent trace.
- No `AgentPlan`, `ToolCall`, `ToolResult`, or `WorldEvent` model.
- No backend tool registry.
- No validated action system; the model cannot propose structured actions yet.
- No persistent world state separate from memory:
  - quests
  - relationships
  - inventory
  - world events
- No planner step between memory/retrieval and final response.
- No `/api/v2/dialogue`.
- Unity only understands v1 response DTOs.
- Unity does not yet display:
  - quest state
  - relationship changes
  - inventory events
  - agent trace/debug panel
- Memory policy is useful but still minimal:
  - no preferred-address superseding
  - no reflection memory type in current write filter
  - no explicit sensitive-content filter
- No self-check/reflection module.
- No systematic eval runner or generated report.

## 4. Current Test Commands

Backend unit/regression tests:

```bash
cd backend
source .venv/bin/activate
python -m pytest -q
python -m unittest discover -s tests
```

Backend health check with server running:

```bash
curl http://127.0.0.1:8008/api/v1/health
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

## 5. Compatibility Rules

These contracts should not be broken by the v2 upgrade:

- `POST /api/v1/dialogue` must keep accepting `DialogueRequest`.
- `dialogue_request.v1` fields must remain compatible with the existing Unity DTO:
  - `schema_version`
  - `session_id`
  - `player_id`
  - `npc_id`
  - `player_text`
  - `distance_m`
  - `is_in_range`
  - `world_state`
- `dialogue_response.v1` must keep returning:
  - `schema_version`
  - `turn_id`
  - `npc_id`
  - `utterances`
  - `internal`
- `Utterance` must keep:
  - `text`
  - `emotion`
  - `action`
  - `delay_ms`
- Existing NPC ids must remain valid:
  - `arknights_amiya`
  - `genshin_yae_miko`
  - `wuwa_jinhsi`
- Existing debug endpoints should remain:
  - `/api/v1/debug/retrieve`
  - `/api/v1/debug/memories`
- Unity should keep v1 fallback until v2 Play Mode smoke is stable.
- `.env`, local SQLite runtime files, Unity generated folders, and unused imported art should stay out of commits.

## 6. Recommended Next Step

Proceed to `docs/09_agent_upgrade_execution_plan.md` Batch 1 Stage 1.2:

```text
Add dialogue_response.v2 agent contract without changing v1 behavior.
```
