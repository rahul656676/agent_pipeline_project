import sqlite3
import json

DB_FILE = "audit_trail.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT UNIQUE,
            user_id TEXT,
            grade INTEGER,
            topic TEXT,
            status TEXT,
            artifact_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_run(run_id: str, user_id: str, grade: int, topic: str, status: str, artifact_dict: dict):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO runs (run_id, user_id, grade, topic, status, artifact_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (run_id, user_id, grade, topic, status, json.dumps(artifact_dict)))
    conn.commit()
    conn.close()

def get_history(user_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT artifact_json FROM runs
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [json.loads(row[0]) for row in rows]
