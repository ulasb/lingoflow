import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from contextlib import asynccontextmanager

from backend import storage
from backend import ollama_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    storage.init_db()
    
    # Initialize scenarios if none exist (we removed the blocking AI call from here)
    # The frontend will now natively command generation if it sees an empty scenario list on load.
    yield

app = FastAPI(lifespan=lifespan)

# Define request/response models
class SettingsUpdate(BaseModel):
    theme: str
    model: str
    practice_language: str
    ui_language: str

class ChatTurn(BaseModel):
    scenario_id: str
    message: str
    
class ChatAbandon(BaseModel):
    scenario_id: str

# Keep a simple in-memory map of active chats to their history ID
# For a production app this would involve sessions/users
active_chats = {}

# --- API Endpoints ---

@app.get("/api/settings")
async def get_settings():
    return storage.get_settings()

@app.post("/api/settings")
async def update_settings(update: SettingsUpdate):
    storage.update_settings(
        theme=update.theme,
        model=update.model,
        practice_language=update.practice_language,
        ui_language=update.ui_language
    )
    return {"success": True}

@app.get("/api/scenarios")
async def get_scenarios():
    return {"scenarios": storage.get_scenarios()}

@app.post("/api/scenarios/generate")
async def generate_scenarios():
    settings = storage.get_settings()
    new_scenarios = await ollama_client.generate_scenarios(
        settings['model'], 
        settings['practice_language'], 
        settings['ui_language']
    )
    if new_scenarios:
        storage.save_scenarios(new_scenarios)
        return {"success": True}
    raise HTTPException(status_code=500, detail="Failed to generate scenarios")

@app.post("/api/chat/turn")
async def process_chat_turn(turn: ChatTurn):
    settings = storage.get_settings()
    scenario = storage.get_scenario(turn.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    # Get or create history
    if turn.scenario_id not in active_chats:
        active_chats[turn.scenario_id] = storage.start_conversation(turn.scenario_id)
        
    history_id = active_chats[turn.scenario_id]
    
    # Save user message
    storage.append_conversation(history_id, "User", turn.message)
    
    # Get total history to pass to bot
    history = storage.get_conversation(history_id)
    
    # Generate bot response
    bot_response = await ollama_client.chat_turn(
        model=settings['model'],
        practice_language=settings['practice_language'],
        ui_language=settings['ui_language'],
        setting=scenario['setting'],
        goal=scenario['goal'],
        history=history,
        user_message=turn.message
    )
    
    # Save bot message
    storage.append_conversation(history_id, "Bot", bot_response)
    
    # Update history for evaluation check
    history.append({"speaker": "Bot", "content": bot_response})
    
    # Check if goal is reached
    is_reached = await ollama_client.evaluate_goal(
        model=settings['model'],
        goal=scenario['goal'],
        history=history
    )
    
    status = "REACHED" if is_reached else "PENDING"
    
    if is_reached:
        storage.mark_conversation_completed(history_id)
        storage.update_settings(add_score=1)
        del active_chats[turn.scenario_id]
        
    return {
        "bot_message": bot_response,
        "status": status
    }

@app.post("/api/chat/abandon")
async def abandon_chat(abandon: ChatAbandon):
    if abandon.scenario_id in active_chats:
        history_id = active_chats[abandon.scenario_id]
        storage.abandon_conversation(history_id)
        del active_chats[abandon.scenario_id]
    return {"success": True}

@app.post("/api/chat/hint")
async def get_hint(abandon: ChatAbandon):
    settings = storage.get_settings()
    scenario = storage.get_scenario(abandon.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    history_id = active_chats.get(abandon.scenario_id)
    history = storage.get_conversation(history_id) if history_id else []
    
    hint = await ollama_client.generate_hint(
         model=settings['model'],
         practice_language=settings['practice_language'],
         ui_language=settings['ui_language'],
         setting=scenario['setting'],
         goal=scenario['goal'],
         history=history
    )
    return {"hint": hint}

# --- Static files matching ---
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Expose clipart files directly
app.mount("/api/clipart", StaticFiles(directory="data/clipart"), name="clipart")

# Serve index.html
@app.get("/")
@app.get("/index.html")
def root():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=f.read())
