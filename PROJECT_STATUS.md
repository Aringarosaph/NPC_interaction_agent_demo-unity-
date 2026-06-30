# NPC RAG Agent Project Status

## Current Decisions

- Repository target: `https://github.com/Aringarosaph/NPC_interaction_agent_demo-unity-`
- Branch: `main`
- Unity editor: `6000.4.2f1`
- Python runtime: `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14`
- GitHub CLI: `/opt/homebrew/bin/gh`
- Unity license: Unity Personal, verified by batchmode editor runs.
- Public character names remain in use for this non-commercial portfolio demo.
- Local secrets, runtime memory, virtual environments, and Unity generated files are not committed.

## Phase Checklist

- [x] Phase 00: repository initialized and source package organized.
- [x] Phase 00: backend virtual environment created and health endpoint verified.
- [x] Phase 01: mock dialogue endpoint verified for all three NPCs.
- [x] Phase 02: retrieval debug endpoint and retrieval tests.
- [x] Phase 03: DeepSeek JSON output integration.
- [x] Phase 04: SQLite memory write/read flow.
- [x] Phase 05: Unity whitebox scene and Play Mode backend dialogue smoke.
- [ ] Phase 06: portfolio polish and demo material.

## Notes For Continuity

- Keep schemas in `schemas/` stable unless the user explicitly approves a schema migration.
- Keep Unity client requests routed through local FastAPI; do not call DeepSeek directly from Unity.
- Responses must remain 1-3 short utterances.
- Cross-world, AI, Unity, backend, and system-prompt questions should hit boundary handling.
- Python dependencies use compatibility ranges because the original scaffold pins tried to build old `scikit-learn==1.6.0` from source on Python 3.14.
- Update this file whenever a phase starts, completes, or changes scope.

## Local Environment Gaps

- `python3` on PATH still points to macOS system Python 3.9.6.
- Use the Python 3.14 path above explicitly until PATH is updated.
- `gh` is installed but `gh auth status` currently reports an invalid token. Git push may still work via Git credentials; otherwise re-authenticate with `gh auth login -h github.com`.

## Validation Log

- 2026-06-30: Created `backend/.venv` with Python 3.14.6.
- 2026-06-30: Installed backend dependencies from `backend/requirements.txt`.
- 2026-06-30: Ran `python -m compileall app` successfully.
- 2026-06-30: Started FastAPI locally on `127.0.0.1:8008`.
- 2026-06-30: `GET /api/v1/health` returned `{"ok":true,"service":"portfolio-npc-rag-agent"}`.
- 2026-06-30: Mock dialogue for `arknights_amiya` asking about `八重神子` returned one utterance and `used_knowledge_ids=["amiya_boundary_other_worlds"]`.
- 2026-06-30: Added `backend/tests/test_mock_dialogue.py` covering all three mock NPC responses and out-of-range schema safety.
- 2026-06-30: Ran `python -m unittest discover -s tests`; 2 tests passed.
- 2026-06-30: Ran `python -m compileall app tests` successfully.
- 2026-06-30: Phase 01 live curl checks passed:
  - `arknights_amiya` / `你知道八重神子吗？` hit `amiya_boundary_other_worlds`.
  - `genshin_yae_miko` / `我想投稿轻小说。` hit `yae_publishing_house`.
  - `wuwa_jinhsi` / `我有一个愿望。` hit `jinhsi_wish_custom`.
- 2026-06-30: Added `GET /api/v1/debug/retrieve?npc_id=...&q=...` for inspectable RAG chunks.
- 2026-06-30: Added pytest retrieval checks for `源石病`, `轻小说投稿`, `今州愿望`, and `阿米娅认识八重神子吗`.
- 2026-06-30: Fixed TF-IDF score mapping so visible chunk filtering cannot misalign chunks and scores.
- 2026-06-30: Ran `python -m pytest -q`; 4 tests and 3 subtests passed.
- 2026-06-30: Phase 02 live curl checks confirmed:
  - `源石病` returned `amiya_oripathy_infected`.
  - `轻小说投稿` returned `yae_publishing_house`.
  - `今州愿望` returned `jinhsi_wish_custom`.
  - `阿米娅认识八重神子吗` returned `amiya_boundary_other_worlds`.
- 2026-06-30: Verified `backend/.env` contains a DeepSeek API key without printing the key.
- 2026-06-30: Direct DeepSeek JSON smoke test returned `{"ok": true, "text": "pong"}`.
- 2026-06-30: Phase 03 live dialogue checks with real DeepSeek passed:
  - `arknights_amiya` / `源石病是什么？` returned 3 JSON utterances and trusted knowledge IDs.
  - `arknights_amiya` / `你认识八重神子吗？` returned boundary refusal JSON.
  - `wuwa_jinhsi` / `我有一个愿望。` returned 2 JSON utterances.
- 2026-06-30: Added LLM client tests for JSON mode, `thinking` disabled, network fallback, and invalid JSON fallback.
- 2026-06-30: Normalizer no longer leaves bubble text ending on a trailing comma when trimming long model output.
- 2026-06-30: Ran `python -m pytest -q`; 9 tests and 3 subtests passed.
- 2026-06-30: Ran `python -m unittest discover -s tests`; 7 tests passed.
- 2026-06-30: Added deterministic preference memory extraction for explicit address requests such as `以后叫我小林`.
- 2026-06-30: Added `GET /api/v1/debug/memories?npc_id=...&player_id=...` for inspectable SQLite memories.
- 2026-06-30: Added isolated SQLite memory tests for write, recall, and NPC-only visibility.
- 2026-06-30: Fixed preference extraction so recall questions like `你记得怎么叫我吗？` do not create a bogus `吗` memory.
- 2026-06-30: Retrieval now returns no chunks for unrelated zero-score queries instead of falling through to high-priority boundary chunks.
- 2026-06-30: Phase 04 live checks passed:
  - `arknights_amiya` / `以后叫我小林` wrote `mem_arknights_amiya_local_player_preferred_address`.
  - `debug/memories` for Amiya returned the `小林` preference.
  - `arknights_amiya` / `你记得怎么叫我吗？` replied with `小林` and created no new memory candidate.
  - `debug/memories` for Yae Miko returned no Amiya player memory.
- 2026-06-30: Ran `python -m pytest -q`; 13 tests and 3 subtests passed.
- 2026-06-30: Ran `python -m unittest discover -s tests`; 9 tests passed.
- 2026-06-30: Unity batchmode license check succeeded with Unity Personal.
- 2026-06-30: Added `unity/PortfolioNpcRagWhitebox` Unity `6000.4.2f1` whitebox project.
- 2026-06-30: Generated `Assets/Scenes/Scene_PortfolioNpcRag.unity` with floor, player capsule, three NPC capsules, third-person camera, dialogue UI, world-space bubbles, and local FastAPI endpoint binding.
- 2026-06-30: Added Unity scene builder and validator menu entries:
  - `NPC Demo > Build Whitebox Scene`
  - `NPC Demo > Validate Whitebox Scene`
- 2026-06-30: Unity batchmode `WhiteboxSceneBuilder.BuildWhiteboxScene` completed successfully.
- 2026-06-30: Unity batchmode `WhiteboxSceneBuilder.ValidateWhiteboxScene` completed successfully with `Whitebox scene validation passed.`
- 2026-06-30: Confirmed `.gitignore` excludes Unity `Library/`, `Temp/`, `Logs/`, and `UserSettings/` under the whitebox project.
- 2026-06-30: Re-ran backend regression checks after Unity project generation:
  - `python -m pytest -q`; 13 tests and 3 subtests passed.
  - `python -m unittest discover -s tests`; 9 tests passed.
- 2026-06-30: Refined Unity whitebox controls:
  - Third-person camera now uses mouse look plus WASD/arrow movement.
  - Chat input now focuses with Enter near an NPC, unlocks the cursor while typing, and exits with Send/Enter/Escape.
  - NPC nameplates now sit above the capsules and speech bubbles sit above the nameplates.
- 2026-06-30: Unity batchmode `WhiteboxSceneBuilder.BuildWhiteboxScene` completed successfully after control and nameplate refinements.
- 2026-06-30: Unity batchmode `WhiteboxSceneBuilder.ValidateWhiteboxScene` completed successfully with `Whitebox scene validation passed.`
- 2026-06-30: Re-ran backend regression checks after Unity control refinements:
  - `python -m pytest -q`; 13 tests and 3 subtests passed.
  - `python -m unittest discover -s tests`; 9 tests passed.
- 2026-06-30: Added MIT license for project code and documentation.
- 2026-06-30: Added Noto Sans CJK SC Regular under SIL Open Font License 1.1 for Unity Chinese UI text, with local license/source notices.
- 2026-06-30: Unity batchmode `WhiteboxSceneBuilder.BuildWhiteboxScene` completed successfully after Chinese font wiring.
- 2026-06-30: Unity batchmode `WhiteboxSceneBuilder.ValidateWhiteboxScene` completed successfully with all TMP text bound to the Chinese font asset.
- 2026-06-30: Backend live checks passed while serving on `127.0.0.1:8008`:
  - `GET /api/v1/health` returned `{"ok":true,"service":"portfolio-npc-rag-agent"}`.
  - `POST /api/v1/dialogue` for `arknights_amiya` returned 3 utterances with `used_knowledge_ids=["amiya_rhodes_mission"]`.
- 2026-06-30: Added Unity Play Mode backend smoke:
  - `BackendDialoguePlayModeSmoke.Run` opens `Scene_PortfolioNpcRag`, enters Play Mode, sends a real Unity client request to local FastAPI, validates the NPC response, and exits with a batchmode status code.
  - Smoke run completed with `Unity backend Play Mode smoke passed.` and backend logged `POST /api/v1/dialogue HTTP/1.1" 200 OK`.
- 2026-06-30: Added `WhiteboxSceneBuilder.ClearChineseFontDynamicData` so Play Mode smoke clears TMP runtime glyph cache before exit and keeps font asset diffs clean.
- 2026-06-30: Rewrote the root `README.md` as an interviewer-facing product guide with project overview, highlights, quick start, backend on/off commands, recording flow, API example, validation commands, layout, and licensing notes.
