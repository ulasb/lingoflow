# LingoFlow
LingoFlow is a desktop-like web app that allows you to engage in short, scenario-based daily life language practice sessions using local Large Language Models via Ollama (specifically designed with Gemma models in mind).

## Setup
1. Ensure Ollama is running (`brew install ollama`, `ollama run gemma3:4b`).
2. Set up the Python environment: `python3 -m venv .venv && source .venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Start the server: `export PYTHONPATH=. && uvicorn backend.main:app --reload`
5. Open your browser to `http://127.0.0.1:8000`.

## Current Progress
*   **Infrastructure Strategy**: Scaffolding complete; project runs fully offline hitting a local Ollama process.
*   **Storage Framework**: SQLite (`lingoflow.db`) efficiently manages state, storing active scenarios, chat logs, user score, and theme configurations. 
*   **UI/UX Aesthetic**: Implemented the primary Dashboard and Chat interfaces utilizing high-end, responsive aesthetics adapted from previous desktop-like local projects. Contains auto-resizing dark/light modes.
*   **Workflow Integration**: 
     - Scenario generation pulls from `.txt` templates containing dynamic targets (setting the `description`, `goal`, and mapping a thematic `clipart` automatically).
     - Chat interactions successfully trigger LLM evaluations on each turn to deterministically check if the user has reached their assigned `goal`. 

## Next Steps / Known Issues
*   **Conversation Clipart Generation**: The current offline system gracefully defaults to simple `.png` squares when missing maps. Next steps include using offline image generation scripts to batch hundreds of varied contextual cliparts (e.g. `florist`, `subway_platform`) for future scenarios to pull dynamically.
*   **Bot Resistance**: The Chat Prompt logic needs to be significantly tightened. In current testing, the bot roleplays slightly too permissively and accommodates the scenario goal immediately (e.g., offering to sell snacks even if the user just responds with "Hi", which tricks the evaluator into automatically terminating and completing the chat successfully!). We will focus heavily on refining the prompt to make the bot wait strictly for the user to explicitly negotiate their own goal.
