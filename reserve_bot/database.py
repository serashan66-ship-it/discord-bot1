import sqlite3
import os
from datetime import datetime

DB_NAME = os.path.join(os.path.dirname(__file__), "reserve.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 🔥 強制的に作り直す
    c.execute("DROP TABLE IF EXISTS reservations")

    c.execute("""
        CREATE TABLE reservations (
            date TEXT,
            time TEXT,
            user_id INTEGER,
            locked INTEGER DEFAULT 0,
            PRIMARY KEY (date, time)
        )
    """)

    conn.commit()
    conn.close()

def get_today():
    return datetime.now().strftime("%Y-%m-%d")

def get_reservation(date, time):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id, locked FROM reservations WHERE date=? AND time=?", (date, time))
    row = c.fetchone()
    conn.close()
    return row

def set_reservation(date, time, user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO reservations(date, time, user_id, locked)
        VALUES (?, ?, ?, 0)
    """, (date, time, user_id))
    conn.commit()
    conn.close()

def clear_reservation(date, time):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM reservations WHERE date=? AND time=?", (date, time))
    conn.commit()
    conn.close()