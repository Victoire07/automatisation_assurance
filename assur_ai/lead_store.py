import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "leads.db"

def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        session_id TEXT NOT NULL,
        intent TEXT,
        score TEXT NOT NULL,
        name TEXT,
        email TEXT,
        phone TEXT,
        consent INTEGER NOT NULL,
        summary TEXT,
        data_json TEXT
    );
    """)
    conn.commit()
    conn.close()

def insert_lead(row: Dict[str, Any]) -> int:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO leads
        (created_at, session_id, intent, score, name, email, phone, consent, summary, data_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        row["created_at"],
        row["session_id"],
        row.get("intent"),
        row["score"],
        row.get("name"),
        row.get("email"),
        row.get("phone"),
        1 if row.get("consent") else 0,
        row.get("summary"),
        row.get("data_json"),
    ))
    conn.commit()
    lead_id = cur.lastrowid
    conn.close()
    return lead_id

def list_leads(limit: int = 50) -> List[Dict[str, Any]]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, created_at, session_id, intent, score, name, email, phone, consent, summary
        FROM leads
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_lead(lead_id: int) -> Optional[Dict[str, Any]]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM leads
        WHERE id = ?
    """, (lead_id,))
    r = cur.fetchone()
    conn.close()
    return dict(r) if r else None
