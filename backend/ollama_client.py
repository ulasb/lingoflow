import os
import json
import httpx
from typing import List, Dict

OLLAMA_BASE_URL = "http://localhost:11434/api"

_client: httpx.AsyncClient = None

def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=120.0)
    return _client

def load_prompt(filename: str) -> str:
    path = os.path.join("prompts", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def clean_json_response(response_text: str) -> str:
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    elif response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    return response_text.strip()

async def get_available_models() -> List[Dict]:
    try:
        res = await get_client().get(f"{OLLAMA_BASE_URL}/tags")
        if res.status_code == 200:
            data = res.json()
            return [
                {
                    "name": m['name'],
                    "parameter_size": m.get('details', {}).get('parameter_size', '')
                }
                for m in data.get('models', [])
            ]
    except Exception:
        pass
    return []

async def generate_scenarios(model: str, practice_language: str, ui_language: str, count: int = 5) -> List[Dict]:
    prompt_template = load_prompt("generate_scenarios.txt")
    prompt = prompt_template.format(practice_language=practice_language, ui_language=ui_language, count=count)
    
    try:
        res = await get_client().post(
            f"{OLLAMA_BASE_URL}/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            }
        )
        data = res.json()
        response_text = data.get("response", "[]")
        clean_str = clean_json_response(response_text)
        scenarios = json.loads(clean_str)
        
        # Simple validation
        if not isinstance(scenarios, list):
            return []
        
        # Check for clipart map; if LLM output isn't a real file, fallback to default.
        for val in scenarios:
            clipart_name = val.get('clipart', 'default_conversation.png')
            if not os.path.exists(os.path.join("data", "clipart", clipart_name)):
                val['clipart'] = "default_conversation.png"
                 
        return scenarios
    except Exception as e:
        print(f"Error generating scenarios: {e}")
        return []

async def chat_turn(model: str, practice_language: str, ui_language: str, setting: str, goal: str, history: List[Dict], user_message: str) -> str:
    sys_prompt_template = load_prompt("chat_system_prompt.txt")
    sys_prompt = sys_prompt_template.format(
        practice_language=practice_language, 
        ui_language=ui_language, 
        scenario_setting=setting, 
        scenario_goal=goal
    )
    
    messages = [{"role": "system", "content": sys_prompt}]
    for turn in history:
        messages.append({"role": "user" if turn['speaker'] == 'User' else "assistant", "content": turn['content']})
        
    messages.append({"role": "user", "content": user_message})
    
    try:
        res = await get_client().post(
            f"{OLLAMA_BASE_URL}/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False
            }
        )
        data = res.json()
        return data["message"]["content"]
    except Exception as e:
        print(f"Error in chat turn: {e}")
        return "I'm sorry, I'm having trouble thinking."

async def evaluate_goal(model: str, goal: str, history: List[Dict]) -> bool:
    prompt_template = load_prompt("goal_evaluation.txt")
    
    history_str = ""
    for turn in history:
        history_str += f"{turn['speaker']}: {turn['content']}\n"
        
    prompt = prompt_template.format(scenario_goal=goal, conversation_history=history_str)
    
    try:
        res = await get_client().post(
            f"{OLLAMA_BASE_URL}/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            }
        )
        data = res.json()
        response_text = data.get("response", "").strip().upper()
        return "REACHED" in response_text
    except Exception as e:
        print(f"Error evaluating goal: {e}")
        return False

async def generate_hint(model: str, practice_language: str, ui_language: str, setting: str, goal: str, history: List[Dict]) -> str:
    prompt_template = load_prompt("hint_generation.txt")
    
    history_str = ""
    for turn in history:
        history_str += f"{turn['speaker']}: {turn['content']}\n"
        
    prompt = prompt_template.format(
        practice_language=practice_language,
        ui_language=ui_language,
        scenario_setting=setting,
        scenario_goal=goal,
        conversation_history=history_str
    )
    
    try:
        res = await get_client().post(
            f"{OLLAMA_BASE_URL}/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            }
        )
        data = res.json()
        return data.get("response", "Could not generate a hint.")
    except Exception as e:
        print(f"Error generating hint: {e}")
        return "Error loading hint."
