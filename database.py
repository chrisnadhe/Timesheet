import sqlite3
from datetime import datetime

DB_FILE = "timesheet.db"

def init_db():
    """Initializes the database by creating tables if they do not exist."""
    conn = sqlite3.connect(DB_FILE)
    try:
        cursor = conn.cursor()
        # Create timesheets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timesheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project TEXT NOT NULL,
                duration REAL NOT NULL,
                description TEXT NOT NULL,
                date TEXT NOT NULL,          -- Format: YYYY-MM-DD
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Create settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY,
                reminder_time TEXT DEFAULT '17:00',  -- Format: HH:MM
                reminder_enabled INTEGER DEFAULT 1   -- 1 = ON, 0 = OFF
            );
        """)
        conn.commit()
    finally:
        conn.close()

def add_timesheet(project: str, duration: float, description: str, date_str: str) -> int:
    """Adds a new timesheet entry. date_str format: YYYY-MM-DD"""
    conn = sqlite3.connect(DB_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO timesheets (project, duration, description, date)
            VALUES (?, ?, ?, ?)
        """, (project, duration, description, date_str))
        conn.commit()
        last_id = cursor.lastrowid
    finally:
        conn.close()
    return last_id

def get_timesheets(start_date: str, end_date: str = None):
    """
    Get timesheets between start_date and end_date (inclusive).
    Format: YYYY-MM-DD
    If end_date is None, gets timesheets only for start_date.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        if end_date:
            cursor.execute("""
                SELECT project, duration, description, date, created_at 
                FROM timesheets 
                WHERE date BETWEEN ? AND ?
                ORDER BY date ASC, created_at ASC
            """, (start_date, end_date))
        else:
            cursor.execute("""
                SELECT project, duration, description, date, created_at 
                FROM timesheets 
                WHERE date = ?
                ORDER BY created_at ASC
            """, (start_date,))
        rows = [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
    return rows

def get_settings(user_id: int) -> dict:
    """Gets settings for a user. If not found, creates default setting."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT reminder_time, reminder_enabled FROM settings WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        if row is None:
            # Insert default settings
            cursor.execute("""
                INSERT INTO settings (user_id, reminder_time, reminder_enabled)
                VALUES (?, '17:00', 1)
            """, (user_id,))
            conn.commit()
            res = {"reminder_time": "17:00", "reminder_enabled": 1}
        else:
            res = dict(row)
    finally:
        conn.close()
    return res

def update_settings(user_id: int, reminder_time: str = None, reminder_enabled: int = None):
    """Updates user settings (reminder_time and/or reminder_enabled)"""
    conn = sqlite3.connect(DB_FILE)
    try:
        cursor = conn.cursor()
        
        # Ensure settings row exists
        cursor.execute("SELECT 1 FROM settings WHERE user_id = ?", (user_id,))
        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO settings (user_id, reminder_time, reminder_enabled)
                VALUES (?, '17:00', 1)
            """, (user_id,))
            conn.commit()
        
        if reminder_time is not None and reminder_enabled is not None:
            cursor.execute("""
                UPDATE settings 
                SET reminder_time = ?, reminder_enabled = ?
                WHERE user_id = ?
            """, (reminder_time, reminder_enabled, user_id))
        elif reminder_time is not None:
            cursor.execute("""
                UPDATE settings 
                SET reminder_time = ?
                WHERE user_id = ?
            """, (reminder_time, user_id))
        elif reminder_enabled is not None:
            cursor.execute("""
                UPDATE settings 
                SET reminder_enabled = ?
                WHERE user_id = ?
            """, (reminder_enabled, user_id))
            
        conn.commit()
    finally:
        conn.close()
