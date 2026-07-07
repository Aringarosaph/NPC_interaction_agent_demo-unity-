# NPC RAG Agent Project Status

## Current Decisions

- Repository target: `https://github.com/Aringarosaph/NPC_interaction_agent_demo-unity-`
- Branch: `main`
- Unity editor: `6000.4.2f1`
- Python runtime: `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14`
- GitHub CLI: `/opt/homebrew/bin/gh`
- Git LFS: installed and available as `git-lfs/3.7.1`
- Unity license: Unity Personal, verified by batchmode editor runs.
- Public character names remain in use for this non-commercial portfolio demo.
- Local secrets, runtime memory, virtual environments, Unity generated files, and derived memory files are not committed.
- The project now presents one complete Agent demo rather than a multi-version migration.

## Phase Checklist

- [x] Repository initialized and connected to the public GitHub repository.
- [x] Backend virtual environment created and FastAPI health endpoint verified.
- [x] Mock dialogue, DeepSeek JSON mode, RAG retrieval, and SQLite memory implemented.
- [x] Unity playable scene created with third-person movement, NPC range detection, input, nameplates, and speech bubbles.
- [x] Current art scene and character meshes rebound to the dialogue system.
- [x] Backend Agent loop implemented with planner, validated tools, SQLite world state, world events, and trace.
- [x] Unity client integrated with the unified dialogue endpoint and agent debug panel.
- [x] Practical memory policy, response self-check, and behavior eval runner implemented.
- [x] README and interview guide refreshed as interviewer-facing Chinese documentation.
- [x] Public API wording unified around `/api/dialogue` and `/api/health`.
- [x] Unity debug panel reset button clears local demo memory, quest, relationship, inventory, and world event state.

## Public API

- `GET /api/health`
- `POST /api/dialogue`
- `GET /api/debug/retrieve`
- `GET /api/debug/memories`
- `POST /api/debug/reset`

Unity should call only `POST /api/dialogue` for runtime NPC interaction.

## Notes For Continuity

- Keep schemas in `schemas/` stable unless the user explicitly approves a schema migration.
- Keep Unity client requests routed through local FastAPI; do not call DeepSeek directly from Unity.
- Responses must remain 1-3 short utterances.
- Cross-world, AI, Unity, backend, and system-prompt questions should hit boundary handling.
- Keep `.env`, local SQLite runtime files, Unity generated folders, unused imported art, and TMP dynamic font cache out of commits.
- Use Git LFS for large Unity art assets that are intentionally tracked.
- Update this file whenever a phase starts, completes, or changes scope.

## Local Environment Gaps

- `python3` on PATH may still point to macOS system Python. Use the Python 3.14 path above explicitly if needed.
- `gh auth status` previously reported an invalid token. Git push may still work via Git credentials; otherwise re-authenticate with `gh auth login -h github.com`.

## Latest Validation Log

- 2026-07-07: Backend full regression passed:
  - `cd backend && .venv/bin/python -m pytest -q`
  - Result: 40 tests and 3 subtests passed.
- 2026-07-07: Backend unittest discovery passed:
  - `cd backend && .venv/bin/python -m unittest discover -s tests`
  - Result: 36 tests passed, with known non-fatal SQLite ResourceWarnings from process-level app stores.
- 2026-07-07: Python compile check passed:
  - `backend/.venv/bin/python -m compileall backend/app backend/tests eval`
- 2026-07-07: Unity art scene binding refreshed:
  - `ArtSceneDialogueBinder.BindArtSceneDialogue`
  - Result: `Art scene dialogue bindings refreshed.`
- 2026-07-07: Unity scene validation passed:
  - `WhiteboxSceneBuilder.ValidateWhiteboxScene`
  - Result: `Whitebox scene validation passed.`
- 2026-07-07: Behavior eval passed:
  - `backend/.venv/bin/python eval/run_eval.py --backend http://127.0.0.1:8008 --out eval/reports/latest_report.md --json-out eval/reports/latest_report.json`
  - Result: 11/11 cases passed, 13 turns, 100% overall case pass rate.
- 2026-07-07: Unity Play Mode backend smoke passed:
  - `BackendDialoguePlayModeSmoke.Run`
  - Result: Unity client hit `POST /api/dialogue` and logged `Unity backend Play Mode smoke passed.`
- 2026-07-08: Demo reset UI added and validated:
  - `POST /api/debug/reset?player_id=local_player` cleared runtime memory/state while preserving seed memories.
  - `cd backend && .venv/bin/python -m pytest -q`; 42 tests and 3 subtests passed.
  - `cd backend && .venv/bin/python -m unittest discover -s tests`; 38 tests passed, with known non-fatal SQLite ResourceWarnings from process-level app stores.
  - `backend/.venv/bin/python -m compileall backend/app backend/tests eval`; passed.
  - Unity batchmode `ArtSceneDialogueBinder.BindArtSceneDialogue`; completed with `Art scene dialogue bindings refreshed.`
  - Unity batchmode `WhiteboxSceneBuilder.ValidateWhiteboxScene`; passed with `Whitebox scene validation passed.`
  - Unity Play Mode backend smoke hit `POST /api/dialogue` and `POST /api/debug/reset`, then passed with `reset ok.`

## Current User-Facing Summary

This repo is a Unity + FastAPI NPC Agent portfolio demo. It shows three character NPCs in a playable Unity scene and routes player text through a local backend Agent loop with RAG, memory, world state, validated tools, self-check, and traceable Unity debug UI.
