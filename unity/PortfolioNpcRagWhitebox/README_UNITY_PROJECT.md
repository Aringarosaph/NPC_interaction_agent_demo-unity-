# Portfolio NPC RAG Whitebox

Unity project for the local FastAPI NPC dialogue demo.

## Open

Use Unity `6000.4.2f1` and open this folder:

```text
unity/PortfolioNpcRagWhitebox
```

## Generate Scene

After the editor opens and packages import, run:

```text
NPC Demo > Build Whitebox Scene
```

This creates:

- `Assets/Scenes/Scene_PortfolioNpcRag.unity`
- A floor, player capsule, three NPC capsules, nameplates, world-space bubbles, UI input, and dialogue system bindings.

Equivalent batch command:

```bash
"/Applications/Unity/Hub/Editor/6000.4.2f1/Unity.app/Contents/MacOS/Unity" \
  -batchmode \
  -projectPath "unity/PortfolioNpcRagWhitebox" \
  -executeMethod WhiteboxSceneBuilder.BuildWhiteboxScene \
  -quit \
  -logFile -
```

## Validate Scene

The project includes a batch-friendly validator that loads the generated scene and checks the main object/component bindings:

```bash
"/Applications/Unity/Hub/Editor/6000.4.2f1/Unity.app/Contents/MacOS/Unity" \
  -batchmode \
  -projectPath "unity/PortfolioNpcRagWhitebox" \
  -executeMethod WhiteboxSceneBuilder.ValidateWhiteboxScene \
  -quit \
  -logFile -
```

Expected success marker:

```text
Whitebox scene validation passed.
```

## Runtime

Start the backend first:

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8008
```

Then enter Play Mode in Unity:

- Move with WASD or arrow keys.
- Look around with the mouse.
- Approach an NPC until the current NPC label changes.
- Press Enter to focus the input field.
- Type and press Enter or Send.
- Press Escape to leave typing mode and return to camera control.
