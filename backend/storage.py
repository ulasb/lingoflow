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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_scenarios (
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
            completed BOOLEAN DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            history_id INTEGER,
            speaker TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(history_id) REFERENCES history(id) ON DELETE CASCADE
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

def save_scenarios(scenarios, clear=True):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if clear:
        cursor.execute("DELETE FROM active_scenarios")
    
    for s in scenarios:
        cursor.execute(
            "INSERT OR IGNORE INTO active_scenarios (id, setting, goal, description, clipart) VALUES (?, ?, ?, ?, ?)",
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
        "INSERT INTO history (scenario_id) VALUES (?)",
        (scenario_id,)
    )
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_id

def append_conversation(history_id, speaker, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (history_id, speaker, content) VALUES (?, ?, ?)", (history_id, speaker, content))
    conn.commit()
    conn.close()

def get_conversation(history_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT speaker, content FROM messages WHERE history_id = ? ORDER BY id ASC", (history_id,)).fetchall()
    
    # Backwards compatibility for old JSON blob logic (conversations completed before schema update)
    if not rows:
        try:
            row = conn.execute("SELECT transcripts FROM history WHERE id = ?", (history_id,)).fetchone()
            if row and row['transcripts']:
                return json.loads(row['transcripts'])
        except Exception as e:
            # It's better to log exceptions than to ignore them silently.
            print(f"Could not retrieve conversation from old format for history_id={history_id}: {e}")
            pass
            
    conn.close()
    return [dict(r) for r in rows]
    
def mark_conversation_completed(history_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE history SET completed = 1 WHERE id = ?", (history_id,))
    
    scenario_row = cursor.execute("SELECT scenario_id FROM history WHERE id = ?", (history_id,)).fetchone()
    if scenario_row:
        cursor.execute("DELETE FROM active_scenarios WHERE id = ?", (scenario_row[0],))
        
    conn.commit()
    conn.close()

def abandon_conversation(history_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE history_id = ?", (history_id,))
    cursor.execute("DELETE FROM history WHERE id = ?", (history_id,))
    conn.commit()
    conn.close()

def get_incomplete_conversation(scenario_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT id FROM history WHERE scenario_id = ? AND completed = 0 ORDER BY id DESC LIMIT 1", (scenario_id,)).fetchone()
    conn.close()
    return row[0] if row else None

def get_completed_conversations():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, scenario_id, timestamp FROM history WHERE completed = 1 ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
