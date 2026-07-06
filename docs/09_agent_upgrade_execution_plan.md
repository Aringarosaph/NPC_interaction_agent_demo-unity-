# Agent Upgrade Execution Plan

> Status: accepted working plan, created 2026-07-07.
> Scope: upgrade the existing Unity + FastAPI NPC RAG demo into a practical game NPC agent loop.

## 1. Direction

The goal is not to stack agent buzzwords. The goal is to make the demo feel like a small but credible in-game NPC agent system:

```text
Unity player input
-> FastAPI dialogue endpoint
-> NPC profile + RAG + memory + state snapshot
-> planner
-> validated backend tools
-> persisted world events
-> short NPC response
-> Unity dialogue bubbles + state/debug UI
```

The current `dialogue_response.v1` endpoint must remain stable. All new agent behavior will be added through a v2 contract and a separate `/api/v2/dialogue` route before Unity switches to v2 by default with v1 fallback.

## 2. Decisions

- Keep the current scene and character models.
- Keep the three existing NPCs as the demo cast:
  - `arknights_amiya`
  - `genshin_yae_miko`
  - `wuwa_jinhsi`
- Do not add an original NPC pack in this upgrade.
- If a task chain needs extra story material, create it around the existing NPCs and their current demo profiles. Use local data first; use web research only when additional character facts are needed, then document the source in notes.
- README should be interviewer-facing. It should explain what the project is, how to run it, architecture, features, API, and validation. It should not include personal recording instructions.
- Do not implement SFT/DPO dry-run, CI, or broad multi-agent simulation in this upgrade.
- Multi-agent is out of scope except for possible later public world events if it naturally fits after the four batches.
- LLM outputs may propose plans or tool calls, but only backend code can validate and mutate world state.
- Mock/deterministic paths must continue to work without an API key.

## 3. Non-Goals

- No full rewrite of the backend.
- No LangChain or external agent framework.
- No direct LLM calls from Unity.
- No model training, LoRA, DPO, RLHF, PPO, or GRPO implementation.
- No Unity scene/art overhaul.
- No Unity CI.
- No free-form NPC-to-NPC autonomous conversation.

## 4. Batch Plan

### Batch 1: Backend Agent Core

Purpose: create a backend v2 loop that can plan, call validated tools, persist state, and return traceable output.

#### Stage 1.1: Baseline Audit

Create `docs/agent_upgrade_audit.md`.

Include:
- backend entry points
- current orchestrator, retriever, memory store, models, prompt builder, LLM client
- Unity client DTO and request flow
- current tests and validation commands
- schema compatibility rules
- current missing agent capabilities

Validation:

```bash
cd backend
source .venv/bin/activate
python -m pytest -q
python -m unittest discover -s tests
```

Commit target:

```text
docs: audit current agent demo baseline
```

#### Stage 1.2: v2 Data Contract

Add v2 models in `backend/app/models.py` without changing v1 response behavior.

Models:
- `AgentPlan`
- `ToolCall`
- `ToolResult`
- `WorldEvent`
- `AgentTrace`
- `DialogueResponseV2`

Add schema examples:
- `schemas/dialogue_response.v2.example.json`
- `schemas/agent_trace.v1.example.json`

Add tests:
- `backend/tests/test_models_v2.py`

Validation:

```bash
cd backend
source .venv/bin/activate
python -m pytest -q
python -m unittest discover -s tests
```

Commit target:

```text
backend: add dialogue v2 agent contract
```

#### Stage 1.3: Tool Registry

Add a lightweight backend-only tool system under `backend/app/tools/`.

Planned files:
- `backend/app/tools/__init__.py`
- `backend/app/tools/base.py`
- `backend/app/tools/registry.py`
- `backend/app/tools/game_tools.py`

Tool rules:
- all tools are registered by name
- arguments are validated before execution
- read-only tools cannot mutate state
- failed tool calls return structured `ToolResult`
- tools never trust arbitrary LLM output

Initial tools:
- `get_player_state`
- `get_quest_state`
- `start_quest`
- `advance_quest`
- `update_relationship`
- `grant_item`
- `emit_world_event`

Add tests:
- `backend/tests/test_tool_registry.py`

Validation:

```bash
cd backend
source .venv/bin/activate
python -m pytest -q backend/tests/test_tool_registry.py
python -m pytest -q
```

Commit target:

```text
backend: add validated game tool registry
```

#### Stage 1.4: State Store

Add `backend/app/state_store.py` for SQLite world state. Keep it separate from `memory_store.py`.

Tables:
- `player_states`
- `npc_relationships`
- `quest_states`
- `inventory_items`
- `world_events`

Methods:
- `get_player_snapshot(player_id, npc_id)`
- `get_quest_state(player_id, quest_id)`
- `start_quest(player_id, npc_id, quest_id)`
- `advance_quest(player_id, npc_id, quest_id, expected_stage=None)`
- `update_relationship(player_id, npc_id, delta, reason)`
- `grant_item(player_id, item_id, quantity, source_turn_id)`
- `log_world_event(...)`

Then wire game tools to `StateStore`.

Add tests:
- `backend/tests/test_state_store.py`

Validation:

```bash
cd backend
source .venv/bin/activate
python -m pytest -q backend/tests/test_state_store.py backend/tests/test_tool_registry.py
python -m pytest -q
```

Commit target:

```text
backend: persist quest relationship inventory events
```

#### Stage 1.5: Planner and `/api/v2/dialogue`

Add `backend/app/agent_planner.py`.

Add `DialogueOrchestrator.handle_v2(req) -> DialogueResponseV2` while preserving `handle(req) -> DialogueResponse`.

v2 flow:

```text
range check
-> load NPC bundle
-> retrieve knowledge
-> retrieve memory
-> read state snapshot
-> plan tool calls
-> validate and execute tools
-> generate or fallback short utterances
-> write allowed memory candidates
-> return utterances + world_events + trace
```

Fallback planner rules:
- If player accepts help/quest and quest is not started, call `start_quest`.
- If player says the task object was found/returned and quest is active, call `advance_quest` and `update_relationship`.
- If player asks to be called by a name, route through the memory write path.
- Otherwise, no tool call.

Existing-character task seed:
- Use one small task line shared by the existing cast.
- Amiya can frame it as helping with a field record or medical supply note.
- Yae Miko can frame it as a publishing/rumor clue or light-novel manuscript lead.
- Jinxi can frame it as a Jinzhou request or wish-related clue.
- Keep the task simple enough for deterministic tests: accepted -> active -> completed.

Add route:
- `POST /api/v2/dialogue`

Add tests:
- `backend/tests/test_dialogue_v2_agent_flow.py`

Validation:

```bash
cd backend
source .venv/bin/activate
python -m pytest -q backend/tests/test_dialogue_v2_agent_flow.py
python -m pytest -q
curl http://127.0.0.1:8008/api/v1/health
```

Commit target:

```text
backend: add dialogue v2 agent flow
```

### Batch 2: Unity v2 Integration and Debug UI

Purpose: make agent state visible inside the current Unity scene without changing scene art.

#### Stage 2.1: Unity DTO and Client Upgrade

Update Unity DTOs in `Assets/Scripts/NpcDialogue/NpcModels.cs`.

Add:
- `AgentPlanDto`
- `ToolCallDto`
- `ToolResultDto`
- `WorldEventDto`
- `AgentTraceDto`
- `DialogueResponseV2Dto`

Update `NpcDialogueClient`:
- add `useV2Api`
- default to v2
- fallback to v1 if v2 fails
- keep existing v1 behavior intact

Validation:
- Unity compile via batchmode validator.
- Backend tests remain green.

Commit target:

```text
unity: add dialogue v2 client models
```

#### Stage 2.2: Runtime Panels

Add lightweight UI panels to the existing scene:
- quest status
- relationship score
- inventory changes
- agent debug trace

The panels should be compact and practical. They should not alter the art scene layout more than necessary.

Displayed debug fields:
- used knowledge ids
- used memory ids
- plan public reason
- tool calls
- tool results
- world events

Validation:
- editor validator checks required panel objects and refs
- Play Mode smoke can make one v2 request and observe panel text updates

Commit target:

```text
unity: show agent world events and trace
```

### Batch 3: Memory Policy, Self-Check, and Evaluation

Purpose: strengthen behavior quality without overengineering.

#### Stage 3.1: Practical Memory Policy

Add `backend/app/memory_policy.py`.

Implement:
- allowed memory types: `preference`, `promise`, `event`, `relationship`, `reflection`, `fact`
- validation for summary, detail, salience, type, and sensitive implementation leakage
- preferred-address conflict handling: latest active preferred address supersedes old ones
- keep retrieval changes minimal and explainable
- extend debug memory endpoint with `include_superseded`

Do not implement a complex weighting/ranking system unless tests show current retrieval is insufficient.

Add tests:
- `backend/tests/test_memory_policy.py`

Validation:

```bash
cd backend
source .venv/bin/activate
python -m pytest -q backend/tests/test_memory_policy.py backend/tests/test_memory_store.py
python -m pytest -q
```

Commit target:

```text
backend: add practical memory policy
```

#### Stage 3.2: Lightweight Self-Check

Add `backend/app/self_check.py`.

Checks:
- response has 1-3 utterances
- no Markdown list formatting
- no claims of being AI, Unity, backend, or system prompt
- no cross-world knowledge leakage
- failed tool result is not described as success
- quest state is not contradicted

Behavior:
- if check fails and deterministic fallback is available, use fallback
- if LLM retry is added, limit to one retry
- add reflection details to trace when useful

Add tests:
- `backend/tests/test_self_check.py`

Validation:

```bash
cd backend
source .venv/bin/activate
python -m pytest -q backend/tests/test_self_check.py backend/tests/test_dialogue_v2_agent_flow.py
python -m pytest -q
```

Commit target:

```text
backend: add lightweight response self check
```

#### Stage 3.3: Eval Runner

Implement systematic eval in `eval/`.

Planned files:
- `eval/run_eval.py`
- `eval/metrics.py`
- `eval/cases/persona.yaml`
- `eval/cases/rag_boundary.yaml`
- `eval/cases/memory.yaml`
- `eval/cases/tool_use.yaml`
- `eval/cases/quest_flow.yaml`
- `eval/cases/format_safety.yaml`
- `eval/reports/.gitkeep`

Outputs:
- `eval/reports/latest_report.json`
- `eval/reports/latest_report.md`

Metrics:
- persona pass rate
- boundary pass rate
- retrieval hit rate
- tool call accuracy
- world event accuracy
- memory recall rate
- format validity rate
- quest success rate
- average latency

Validation:

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8008
```

```bash
python eval/run_eval.py --backend http://127.0.0.1:8008 --out eval/reports/latest_report.md
```

Commit target:

```text
eval: add agent behavior evaluation runner
```

### Batch 4: Portfolio Documentation and Final Verification

Purpose: make the project understandable to an interviewer in a few minutes.

#### Stage 4.1: README Refresh

Update README as an interviewer-facing project guide.

Include:
- 30-second project introduction
- architecture diagram with Mermaid
- quick start
- backend and Unity run commands
- API examples for v1 and v2
- feature list:
  - persona
  - RAG
  - long-term memory
  - state tracking
  - validated tool use
  - planning
  - self-check/reflection
  - eval
- JD capability mapping table
- latest eval report summary
- limitations
- future work
- licensing notes

Do not include personal recording instructions.

Add:
- `docs/agent_portfolio_interview_guide.md`

Commit target:

```text
docs: refresh portfolio guide for agent demo
```

#### Stage 4.2: Final Local Validation

Run:

```bash
cd backend
source .venv/bin/activate
python -m pytest -q
python -m unittest discover -s tests
```

Run Unity validator:

```bash
"/Applications/Unity/Hub/Editor/6000.4.2f1/Unity.app/Contents/MacOS/Unity" \
  -batchmode \
  -projectPath "unity/PortfolioNpcRagWhitebox" \
  -executeMethod WhiteboxSceneBuilder.ValidateWhiteboxScene \
  -quit \
  -logFile -
```

Run Play Mode smoke with backend running:

```bash
"/Applications/Unity/Hub/Editor/6000.4.2f1/Unity.app/Contents/MacOS/Unity" \
  -batchmode \
  -projectPath "unity/PortfolioNpcRagWhitebox" \
  -executeMethod BackendDialoguePlayModeSmoke.Run \
  -logFile /tmp/npc_unity_playmode_backend_smoke.log
```

Update `PROJECT_STATUS.md` with final results.

Commit target:

```text
chore: record final agent upgrade validation
```

## 5. Commit and Push Policy

- Commit after each meaningful stage.
- Do not push unless the user explicitly asks.
- Keep `.env`, SQLite runtime files, Unity generated folders, and derived memory files out of commits.
- Avoid staging the TMP font dynamic cache unless it is intentionally regenerated and verified.
- Use Git LFS for large Unity art assets already tracked by `.gitattributes`.

## 6. Risk Notes

- Python 3.14 may be too new for some ML/alignment libraries. This is one reason SFT/DPO dry-run is excluded from this upgrade.
- Unity scene serialization can create large diffs. Prefer editor scripts and validators so changes are reproducible.
- v2 should be additive. If v2 fails, Unity should keep v1 fallback until v2 is stable.
- Tool calls must be deterministic enough for tests. LLM-based tool proposals can be added only after deterministic tests pass.
- Keep agent traces concise. Debug UI should be readable, not a wall of JSON.

## 7. Current First Action

Start with Batch 1 Stage 1.1 after this plan is committed.
