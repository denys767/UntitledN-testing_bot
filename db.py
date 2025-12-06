import sqlite3
import asyncio

DB = "bot.db"

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            grad_year INTEGER,
            specialty TEXT,
            coins INTEGER DEFAULT 0,
            role TEXT DEFAULT 'student',
            streak INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

async def add_user(user_id, first, last, year, spec):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users(user_id, first_name, last_name, grad_year, specialty, coins)
        VALUES (?, ?, ?, ?, ?, 0)
    """, (user_id, first, last, year, spec))
    conn.commit()
    conn.close()

async def get_user(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    r = cur.fetchone()
    conn.close()
    return r

async def update_role(user_id, role):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE users SET role=? WHERE user_id=?", (role, user_id))
    conn.commit()
    conn.close()

async def ban_user(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE users SET banned=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

async def update_coins_and_streak(user_id, coins, streak):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE users SET coins=?, streak=? WHERE user_id=?",
                (coins, streak, user_id))
    conn.commit()
    conn.close()

async def get_rating():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT first_name, last_name, coins FROM users ORDER BY coins DESC")
    r = cur.fetchall()
    conn.close()
    return r
