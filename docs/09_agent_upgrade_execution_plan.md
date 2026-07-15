# Agent Upgrade Implementation Plan

> Status: completed implementation record, updated 2026-07-07.
> Scope: turn the Unity + FastAPI NPC RAG demo into a practical game NPC agent loop.

## 1. Direction

The goal is a small but credible in-game NPC agent system:

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

The public runtime contract is intentionally simple:

- `GET /api/health`
- `POST /api/dialogue`
- `GET /api/debug/retrieve`
- `GET /api/debug/memories`

Unity talks to one dialogue endpoint. The backend keeps smaller internal response models only as implementation details for normalization and self-check.

## 2. Decisions

- Keep the current scene and character models.
- Keep the three existing NPCs as the demo cast:
  - `arknights_amiya`
  - `genshin_yae_miko`
  - `wuwa_jinhsi`
- Do not add an original NPC pack in this upgrade.
- If a task chain needs extra story material, create it around the existing NPCs and their current demo profiles.
- README should be interviewer-facing. It should explain what the project is, how to run it, architecture, features, API, validation, and licensing.
- Do not include personal recording instructions in public project docs.
- Do not implement SFT/DPO dry-run, CI, or broad multi-agent simulation in this upgrade.
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

## 4. Completed Batches

### Batch 1: Backend Agent Core

Implemented:

- Agent response models: `AgentPlan`, `ToolCall`, `ToolResult`, `WorldEvent`, `AgentTrace`, `AgentDialogueResponse`.
- JSON schema examples under `schemas/`.
- Backend-only validated tool registry.
- SQLite `StateStore` for player state, relationships, quests, inventory, and world events.
- Deterministic `AgentPlanner`.
- Canonical `DialogueOrchestrator.handle(req) -> AgentDialogueResponse`.
- Unified `POST /api/dialogue`.

The core backend flow is:

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
-> run self-check
-> return utterances + world_events + trace
```

### Batch 2: Unity Integration and Debug UI

Implemented:

- Unity DTOs for the unified agent response.
- `NpcDialogueClient` calling `http://127.0.0.1:8008/api/dialogue`.
- Runtime debug panel showing:
  - quest/world events
  - relationship changes
  - inventory changes
  - planner intent and reason
  - used knowledge and memory ids
  - tool calls and tool results
  - self-check reflection
- Art-scene rebinding through editor automation.
- Unity scene validator and Play Mode backend smoke.

### Batch 3: Memory Policy, Self-Check, and Evaluation

Implemented:

- Practical memory policy for allowed memory types, summary/detail/salience validation, sensitive implementation leakage filtering, and preferred-address superseding.
- `include_superseded` debug inspection for memory audits.
- Lightweight self-check for format, implementation leakage, cross-world leakage, failed-tool success claims, and quest-state contradictions.
- Behavior eval runner in `eval/` with Markdown and JSON reports.

Current eval suites cover:

- persona
- RAG boundary
- memory
- tool use
- quest flow
- format safety

### Batch 4: Portfolio Documentation and Final Verification

Implemented:

- Chinese interviewer-facing root `README.md`.
- `docs/agent_portfolio_interview_guide.md`.
- Current architecture and data-contract docs.
- Final validation log in `docs/PROJECT_STATUS.md`.

## 5. Canonical Contracts

Request schema:

- `schemas/dialogue_request.schema.json`
- `schema_version: dialogue_request.agent`

Response schema:

- `schemas/dialogue_response.schema.json`
- `schema_version: dialogue_response.agent`

Trace example:

- `schemas/agent_trace.example.json`

## 6. Validation Commands

Backend:

```bash
cd backend
source .venv/bin/activate
python -m pytest -q
python -m unittest discover -s tests
```

Compile:

```bash
backend/.venv/bin/python -m compileall backend/app backend/tests eval
```

Eval, with backend running:

```bash
backend/.venv/bin/python eval/run_eval.py \
  --backend http://127.0.0.1:8008 \
  --out eval/reports/latest_report.md \
  --json-out eval/reports/latest_report.json
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

Unity Play Mode backend smoke, with backend running:

```bash
"/Applications/Unity/Hub/Editor/6000.4.2f1/Unity.app/Contents/MacOS/Unity" \
  -batchmode \
  -projectPath "unity/PortfolioNpcRagWhitebox" \
  -executeMethod BackendDialoguePlayModeSmoke.Run \
  -logFile /tmp/npc_unity_playmode_backend_smoke.log
```

## 7. Commit and Push Policy

- Commit after each meaningful stage.
- Push only when the user explicitly asks.
- Keep `.env`, SQLite runtime files, Unity generated folders, and derived memory files out of commits.
- Avoid staging TMP font dynamic cache unless it is intentionally regenerated and verified.
- Use Git LFS for large Unity art assets tracked by `.gitattributes`.

## 8. Risk Notes

- Python 3.14 may be too new for some ML/alignment libraries, which is one reason training experiments are out of scope.
- Unity scene serialization can create large diffs. Prefer editor scripts and validators so changes are reproducible.
- Tool calls must be deterministic enough for tests.
- Keep agent traces concise. Debug UI should be readable, not a wall of JSON.
