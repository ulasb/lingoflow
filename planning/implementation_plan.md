# LingoFlow Implementation Plan

This document outlines the implementation plan for the LingoFlow desktop-like browser application, based on the requirements defined in `initial_definition.md`.

## 1. System Architecture

*   **Backend:** Python via a lightweight web framework (e.g., FastAPI or Flask) to serve the UI and handle API requests.
*   **Frontend:** HTML, CSS, and JavaScript running in a local browser. The UI should be dynamic and responsive, using vanilla JS or a lightweight framework (like Vue.js or Svelte) to handle state (settings, chat, scenarios).
*   **AI Integration:** Ollama running locally. The backend will communicate with the local Ollama REST API.
*   **Data Storage:** A lightweight SQLite database to store user settings, completed conversations, and score.
*   **Prompt Management:** Plain text or Markdown files located in a dedicated `prompts/` directory to separate prompt logic from backend code.

## 2. Core Components

### 2.1 Backend (Python)
*   **Web Server:** Serves the static frontend assets (HTML, CSS, JS, pre-created clipart).
*   **Ollama Client:** Interacts with the local Ollama instance to check available models, generate scenarios, handle chat turns, and provide hints.
*   **Storage Manager:** Reads/writes completed conversations and user settings to the local disk.
*   **Prompt Loader:** Reads `.txt` or `.md` files from the `prompts/` directory.

### 2.2 Frontend (Browser UI)
*   **Main Dashboard:** Displays the current score, settings button, and the 5 dynamically generated daily scenarios.
*   **Chat Interface:** (Will re-use and adapt HTML/CSS/JS design elements and chat dynamics from the local `debating-llms` project)
    *   Displays the scenario setting and goal.
    *   Chat bubbles for user and bot.
    *   Loading indicator ("Thinking...") when waiting for the model.
    *   "HINT" button to suggest the next message.
    *   "Abandon" button to exit the scenario without saving.
*   **History View:** A list of cleared situations that can be clicked to view the full conversation transcript.
*   **Settings Modal:** Controls for Dark/Light mode, Model selection, Practice Language, UI Language, and an About section.
*   **Interactive Text Elements:** Words in bot messages will be clickable to show meanings. For Japanese, text will render with `<ruby>` and `<rt>` tags for furigana.

## 3. Implementation Phases

### Phase 1: Foundation and Setup
1.  **Project Initialization:** Set up the Python virtual environment and project structure (`backend/`, `frontend/`, `prompts/`, `data/`).
2.  **Basic Web Server:** Create a FastAPI/Flask server to serve a dummy `index.html`.
3.  **Ollama Integration:** Create a Python module to connect to Ollama. Verify Ollama installation and ensure Gemma 3 (4B/12B/27B) exists, prompting the user if not.
4.  **Prompt System:** Define the structure for prompt templates (e.g., `generate_scenarios.txt`, `chat_turn.txt`).

### Phase 2: Scenario Generation and Basic UI
1.  **Settings Menu:** Implement the UI and backend logic to parse locally available Gemma 3 models and save settings (UI Language, Practice Language, Theme).
2.  **Scenario Generation Prompt:** Write the prompt to generate 5 daily scenarios with settings and goals.
3.  **Dashboard UI:** Display the generated scenarios and the user's current score (loaded from local data).
4.  **Clipart Integration:** Map pre-created clipart files to the generated scenarios using deterministic logic based on the scenario setting or goal. *(Note: We will later generate a few hundred common theme cliparts—like a train station, a florist, a supermarket, etc.—that can be matched to most generated scenarios).*

### Phase 3: Core Chat Interaction
1.  **Chat Interface:** Build the UI for the back-and-forth chat.
2.  **Chat Logic:** Wire the frontend chat input to the backend Ollama client. Pass the conversation history and scenario goal as context.
3.  **Typing Indicator:** Implement asynchronous requests so the UI shows a "thinking" state while waiting for the Ollama response.
4.  **Goal Tracking:** Prompt the model (or use a secondary evaluation prompt) to detect when the scenario's goal has been reached.
5.  **Abandon / Finish:** Implement the ability to abandon the chat (return to dashboard) or finish it (save to disk, increment score, generate a replacement scenario).

### Phase 4: Advanced Language Features
1.  **Hint System:** Implement the "HINT" button utilizing a specific prompt (`hint.txt`) to generate a suggested response and explanation in the target UI language.
2.  **Furigana Rendering:** For Japanese, update the bot's generation or use a post-processing step (via a library like `pykakasi` or purely via the LLM) to output text with furigana using HTML `<ruby>` tags.
3.  **Clickable Dictionary:** Process bot messages so each word is wrapped in an HTML element (e.g., `<span>`). Bind click events to a backend endpoint that looks up the word's meaning in the chosen UI language (potentially using a dictionary API or a secondary LLM query).

### Phase 5: Polish and Non-Functional Requirements
1.  **Performance Optimization:** Ensure streaming responses from Ollama if necessary to keep response times under a few seconds and improve perceived latency.
2.  **State Persistence:** Ensure all cleared situations are reliably saved and can be viewed in the History View.
3.  **Theming:** Finalize Dark / Light / System Default CSS.
4.  **Testing & Error Handling:** Handle cases where Ollama is offline or the model throws an error.

## 4. Required Dependencies
*   `fastapi` / `flask` (Backend server)
*   `uvicorn` (ASGI server, if using FastAPI)
*   `requests` or `httpx` (For Ollama API calls)
*   Frontend: Vanilla JS + CSS or lightweight framework (Vue/Alpine.js).

## 5. Directory Structure
```
lingoflow/
├── backend/
│   ├── main.py
│   ├── ollama_client.py
│   ├── storage.py
│   └── language_utils.py
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── prompts/
│   ├── generate_scenarios.txt
│   ├── chat_system_prompt.txt
│   ├── goal_evaluation.txt
│   └── hint_generation.txt
├── data/
│   ├── lingoflow.db
│   └── clipart/
├── planning/
│   ├── initial_definition.md
│   └── implementation_plan.md
└── requirements.txt
```
