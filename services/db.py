import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "interview_data.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            question_id TEXT NOT NULL,
            question_text TEXT NOT NULL,
            transcript TEXT,
            content_score REAL,
            keyword_coverage REAL,
            filler_count INTEGER,
            engagement_score REAL,
            smile_score REAL,
            overall_score REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    """)
    conn.commit()
    conn.close()


def create_session(role):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sessions (role, created_at) VALUES (?, ?)",
        (role, datetime.utcnow().isoformat())
    )
    conn.commit()
    session_id = cur.lastrowid
    conn.close()
    return session_id


def save_attempt(session_id, question_id, question_text, transcript, scores):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO attempts
        (session_id, question_id, question_text, transcript, content_score,
         keyword_coverage, filler_count, engagement_score, smile_score, overall_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id, question_id, question_text, transcript,
        scores["content_score"], scores["keyword_coverage"], scores["filler_count"],
        scores["engagement_score"], scores["smile_score"], scores["overall_score"],
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()


def get_session_attempts(session_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM attempts WHERE session_id = ? ORDER BY id ASC", (session_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session(session_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_sessions_summary():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, s.role, s.created_at,
               AVG(a.overall_score) as avg_score,
               COUNT(a.id) as question_count
        FROM sessions s
        LEFT JOIN attempts a ON s.id = a.session_id
        GROUP BY s.id
        ORDER BY s.id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
