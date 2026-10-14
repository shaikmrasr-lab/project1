"""
Smart Campus AI - Database Layer
Uses standard library sqlite3 for zero-dependency persistence.
Handles schema migrations, seed data, and data access methods.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_campus.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # User Profile
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        student_id TEXT NOT NULL,
        major TEXT NOT NULL,
        semester TEXT NOT NULL,
        gpa REAL DEFAULT 3.82,
        attendance_pct REAL DEFAULT 94.2,
        streak_days INTEGER DEFAULT 7,
        daily_goal_hours REAL DEFAULT 4.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Courses
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        instructor TEXT NOT NULL,
        room TEXT NOT NULL,
        credits INTEGER DEFAULT 3,
        color TEXT DEFAULT '#4f46e5'
    )
    """)

    # Daily Classes / Timetable
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT NOT NULL,
        day_of_week TEXT NOT NULL,  -- Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
        start_time TEXT NOT NULL,   -- e.g. "09:00"
        end_time TEXT NOT NULL,     -- e.g. "10:30"
        room TEXT NOT NULL,
        professor TEXT NOT NULL,
        topic TEXT
    )
    """)

    # Tasks
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        course_code TEXT NOT NULL,
        due_date TEXT NOT NULL,     -- ISO string YYYY-MM-DDTHH:MM
        priority TEXT DEFAULT 'Medium', -- Urgent, High, Medium, Low
        status TEXT DEFAULT 'pending',  -- pending, in_progress, completed
        estimated_minutes INTEGER DEFAULT 60,
        completed_at TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Upcoming Deadlines & Examinations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deadlines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        course_code TEXT NOT NULL,
        type TEXT DEFAULT 'Assignment', -- Exam, Assignment, Project, Quiz
        deadline_date TEXT NOT NULL,     -- ISO string YYYY-MM-DDTHH:MM
        weight_pct INTEGER DEFAULT 15,
        location TEXT,
        description TEXT,
        status TEXT DEFAULT 'upcoming'   -- upcoming, submitted, graded
    )
    """)

    # Campus Announcements
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,         -- Academic, Examination, Events, Timetable, General
        author TEXT NOT NULL,
        date TEXT NOT NULL,
        content TEXT NOT NULL,
        is_pinned INTEGER DEFAULT 0,
        is_urgent INTEGER DEFAULT 0,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Study Plans
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS study_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        subjects_json TEXT NOT NULL,
        available_hours REAL NOT NULL,
        technique TEXT DEFAULT 'Pomodoro (25/5)',
        plan_json TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Notes & Summaries & Practice Quizzes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        course_code TEXT NOT NULL,
        original_text TEXT NOT NULL,
        summary TEXT NOT NULL,
        key_takeaways_json TEXT NOT NULL,
        quiz_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Chatbot messages
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,            -- user or assistant
        message TEXT NOT NULL,
        context_type TEXT DEFAULT 'general', -- general, doc, schedule, task
        source_doc TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Study logs for analytics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS study_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,            -- YYYY-MM-DD
        subject TEXT NOT NULL,
        minutes_studied INTEGER NOT NULL,
        technique TEXT DEFAULT 'Pomodoro',
        notes TEXT
    )
    """)

    # System settings (API key, theme, etc.)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

def query_db(query, args=(), one=False):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    r = cur.fetchall()
    conn.close()
    return (dict(r[0]) if r else None) if one else [dict(row) for row in r]

def execute_db(query, args=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    last_id = cur.lastrowid
    conn.commit()
    conn.close()
    return last_id

def get_setting(key, default=None):
    row = query_db("SELECT value FROM settings WHERE key = ?", (key,), one=True)
    return row['value'] if row else default

def set_setting(key, value):
    execute_db("""
    INSERT INTO settings (key, value) VALUES (?, ?)
    ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, str(value)))
