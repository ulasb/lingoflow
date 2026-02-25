import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
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

# Remove in-memory state tracking for active_chats, relying seamlessly on SQLite lookup.

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

@app.get("/api/models")
async def get_models():
    models = await ollama_client.get_available_models()
    return {"models": models}

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
async def process_chat_turn(turn: ChatTurn, background_tasks: BackgroundTasks):
    settings = storage.get_settings()
    scenario = storage.get_scenario(turn.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    # Get or create history
    history_id = storage.get_incomplete_conversation(turn.scenario_id)
    if not history_id:
        history_id = storage.start_conversation(
            turn.scenario_id,
            practice_language=settings['practice_language'],
            model=settings['model']
        )
    
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
    
    conversation_summary = None
    if is_reached:
        # Get full history including the final bot message for accurate summary
        full_history = storage.get_conversation(history_id)
        storage.mark_conversation_completed(history_id)
        storage.update_settings(add_score=1)
        background_tasks.add_task(generate_replacement_scenario, settings)
        # Generate summary synchronously so it can be returned in the response
        try:
            conversation_summary = await ollama_client.generate_conversation_summary(
                model=settings['model'],
                practice_language=settings['practice_language'],
                ui_language=settings['ui_language'],
                goal=scenario['goal'],
                history=full_history
            )
            storage.save_conversation_summary(history_id, conversation_summary)
        except Exception as e:
            print(f"Failed to generate conversation summary inline: {e}")
        
    return {
        "bot_message": bot_response,
        "status": status,
        "summary": conversation_summary
    }

async def generate_replacement_scenario(settings):
    try:
        new_scen = await ollama_client.generate_scenarios(
            settings['model'], 
            settings['practice_language'], 
            settings['ui_language'],
            count=1
        )
        if new_scen:
            storage.save_scenarios(new_scen, clear=False)
    except Exception as e:
        print(f"Failed to generate replacement scenario: {e}")



@app.post("/api/chat/abandon")
async def abandon_chat(abandon: ChatAbandon):
    history_id = storage.get_incomplete_conversation(abandon.scenario_id)
    if history_id:
        storage.abandon_conversation(history_id)
    return {"success": True}

@app.post("/api/chat/hint")
async def get_hint(abandon: ChatAbandon):
    settings = storage.get_settings()
    scenario = storage.get_scenario(abandon.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    history_id = storage.get_incomplete_conversation(abandon.scenario_id)
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

@app.get("/api/history")
async def get_history():
    return {"history": storage.get_completed_conversations()}

@app.get("/api/history/{history_id}")
async def get_history_detail(history_id: int):
    # Simply retrieve the array. The history_id acts as the existence check, and an empty list is valid.
    conversation = storage.get_conversation(history_id)
    return {"conversation": conversation}

@app.get("/api/history/{history_id}/summary")
async def get_history_summary(history_id: int):
    summary = storage.get_conversation_summary(history_id)
    return {"summary": summary}

@app.delete("/api/history/{history_id}")
async def delete_history_item(history_id: int):
    storage.delete_conversation(history_id)
    return {"success": True}

@app.delete("/api/history")
async def delete_all_history():
    storage.delete_all_conversations()
    return {"success": True}

# --- Static files matching ---
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Expose clipart files directly
app.mount("/api/clipart", StaticFiles(directory="data/clipart"), name="clipart")

# Serve index.html
@app.get("/")
@app.get("/index.html")
def root():
    return FileResponse("frontend/index.html")
