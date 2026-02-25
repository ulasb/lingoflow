# LingoFlow
LingoFlow is a desktop-like web app that allows you to engage in short, scenario-based daily life language practice sessions using local Large Language Models via Ollama (specifically designed with Gemma models in mind).

## Setup
1. Ensure Ollama is running (`brew install ollama`, `ollama run gemma3:4b`).
2. Set up the Python environment: `python3 -m venv .venv && source .venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Start the server: `export PYTHONPATH=. && uvicorn backend.main:app --reload`
5. Open your browser to `http://127.0.0.1:8000`.

## Model Recommendations
LingoFlow is designed around **multilingual models** that can carry natural conversations in the target language. If your hardware can't run a capable local model, Ollama supports cloud-hosted models as a drop-in alternative.

**Recommended local models:**
- `gemma3:4b` — Good balance of quality and speed on most modern Macs.
- `gemma3:12b` or larger — Better multilingual quality if your GPU/CPU can handle it.

**Cloud-hosted option (via Ollama):**
- [`gemini2.0-flash-preview:gemini-2.0-flash-preview-04-17`](https://ollama.com/library/gemini2.0-flash-preview) — Runs through Google's API via Ollama (no local GPU needed). Excellent multilingual capability. Requires setting up an Ollama API key.
  ```
  ollama run gemini2.0-flash-preview:gemini-2.0-flash-preview-04-17
  ```
  > ⚠️ **Note:** Some cloud-hosted models may require a Google AI subscription or API quota. Check the [Ollama model page](https://ollama.com/library/gemini2.0-flash-preview) for details.


## Current Progress
*   **Infrastructure Strategy**: Scaffolding complete; project runs fully offline hitting a local Ollama process.
*   **Storage Framework**: SQLite (`lingoflow.db`) efficiently manages state, storing active scenarios, chat logs, user score, and theme configurations. 
*   **UI/UX Aesthetic**: Implemented the primary Dashboard and Chat interfaces utilizing high-end, responsive aesthetics adapted from previous desktop-like local projects. Contains auto-resizing dark/light modes.
*   **Workflow Integration**:
     - Scenario generation pulls from `.txt` templates containing dynamic targets (setting the `description`, `goal`, and mapping a thematic `clipart` automatically).
     - Chat interactions successfully trigger LLM evaluations on each turn to deterministically check if the user has reached their assigned `goal`.
     - Integrated a comprehensive **History** log that tracks completed chat sessions and rendering detailed historical chat transcripts for review.
*   **Prompt Engineering**: Enhanced Bot Resistance constraints. The bot now explicitly waits passively for a user to negotiate requests naturally instead of prematurely handing them the goal scenario.

## Next Steps / Known Issues
*   **Conversation Clipart Generation**: The current offline system gracefully defaults to simple `.png` squares when missing maps. Next steps include using offline image generation scripts to batch hundreds of varied contextual cliparts (e.g. `florist`, `subway_platform`) for future scenarios to pull dynamically.
