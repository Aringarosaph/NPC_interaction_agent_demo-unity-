# Backend Scaffold

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```

In this workspace, the verified Python 3.14 interpreter is:

```bash
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14
```

Use it when creating the local virtual environment if `python3` still points to macOS system Python.

For real DeepSeek output, set `DEEPSEEK_API_KEY` in `backend/.env`. The file is ignored by git.

Server: `http://127.0.0.1:8008`

Health check:

```bash
curl http://127.0.0.1:8008/api/v1/health
```

Dialogue test:

```bash
curl -X POST http://127.0.0.1:8008/api/v1/dialogue \
  -H "Content-Type: application/json" \
  -d '{"schema_version":"dialogue_request.v1","session_id":"s1","player_id":"local_player","npc_id":"arknights_amiya","player_text":"你知道八重神子吗？","distance_m":2.0,"is_in_range":true,"world_state":{"location_id":"portfolio_whitebox_room","game_time_label":"demo","quest_stage":0,"relationship_score":0,"debug_enabled":true}}'
```

Mock dialogue regression tests:

```bash
python -m unittest discover -s tests
python -m pytest -q
```

Retrieval debug endpoint:

```bash
curl "http://127.0.0.1:8008/api/v1/debug/retrieve?npc_id=arknights_amiya&q=源石病"
```

DeepSeek JSON smoke test:

```bash
curl -X POST http://127.0.0.1:8008/api/v1/dialogue \
  -H "Content-Type: application/json" \
  -d '{"schema_version":"dialogue_request.v1","session_id":"deepseek_smoke","player_id":"local_player","npc_id":"wuwa_jinhsi","player_text":"我有一个愿望。","distance_m":2.0,"is_in_range":true,"world_state":{"location_id":"portfolio_whitebox_room","game_time_label":"demo","quest_stage":0,"relationship_score":0,"debug_enabled":true}}'
```
