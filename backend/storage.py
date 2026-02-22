import sqlite3
import json
import os

DB_PATH = os.path.join("data", "lingoflow.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            theme TEXT DEFAULT 'system',
            model TEXT DEFAULT 'gemma3:4b',
            practice_language TEXT DEFAULT 'Japanese',
            ui_language TEXT DEFAULT 'English',
            score INTEGER DEFAULT 0
        )
    """)
    
    # Ensure a single row exists for settings
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO settings (id) VALUES (1)")
        
    # Active Scenarios table
    cursor.execute("DROP TABLE IF EXISTS active_scenarios")
    cursor.execute("""
        CREATE TABLE active_scenarios (
            id TEXT PRIMARY KEY,
            setting TEXT,
            goal TEXT,
            description TEXT,
            clipart TEXT
        )
    """)
    
    # Conversations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario_id TEXT,
            transcripts TEXT,
            completed BOOLEAN DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def get_settings():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else {}

def update_settings(theme=None, model=None, practice_language=None, ui_language=None, add_score=0):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if theme:
        updates.append("theme = ?")
        params.append(theme)
    if model:
        updates.append("model = ?")
        params.append(model)
    if practice_language:
        updates.append("practice_language = ?")
        params.append(practice_language)
    if ui_language:
        updates.append("ui_language = ?")
        params.append(ui_language)
    if add_score > 0:
        updates.append("score = score + ?")
        params.append(add_score)
        
    if updates:
        params.append(1) # id=1
        query = f"UPDATE settings SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    conn.close()

def save_scenarios(scenarios):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM active_scenarios")
    
    for s in scenarios:
        cursor.execute(
            "INSERT INTO active_scenarios (id, setting, goal, description, clipart) VALUES (?, ?, ?, ?, ?)",
            (s['id'], s['setting'], s['goal'], s.get('description', ''), s['clipart'])
        )
    conn.commit()
    conn.close()

def get_scenarios():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM active_scenarios").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_scenario(scenario_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM active_scenarios WHERE id = ?", (scenario_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def start_conversation(scenario_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO history (scenario_id, transcripts) VALUES (?, ?)",
        (scenario_id, json.dumps([]))
    )
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_id

def append_conversation(history_id, speaker, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    row = cursor.execute("SELECT transcripts FROM history WHERE id = ?", (history_id,)).fetchone()
    
    if row:
        transcripts = json.loads(row[0])
        transcripts.append({"speaker": speaker, "content": content})
        cursor.execute("UPDATE history SET transcripts = ? WHERE id = ?", (json.dumps(transcripts), history_id))
        conn.commit()
    conn.close()

def get_conversation(history_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT transcripts FROM history WHERE id = ?", (history_id,)).fetchone()
    conn.close()
    return json.loads(row[0]) if row else []
    
def mark_conversation_completed(history_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE history SET completed = 1 WHERE id = ?", (history_id,))
    
    # remove the scenario so it gets regenerated later if needed, or simply let frontend regenerate all
    # For now we'll just keep it in active_scenarios and let the user re-generate explicitly or when empty.
    conn.commit()
    conn.close()

def abandon_conversation(history_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history WHERE id = ?", (history_id,))
    conn.commit()
    conn.close()
