import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

def connect():
    return sqlite3.connect("chat.db")

def init_db():
    conn = connect()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        status TEXT,
        last_seen TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        msg TEXT,
        type TEXT
    )
    """)

    conn.commit()
    conn.close()

def create_user(username, password):
    conn = connect()
    c = conn.cursor()

    try:
        c.execute("INSERT INTO users VALUES (?,?,?,?)",
        (username, generate_password_hash(password),"En línea",""))
        conn.commit()
        return True
    except:
        return False

def check_user(username, password):
    conn = connect()
    c = conn.cursor()

    c.execute("SELECT password FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()

    if result:
        return check_password_hash(result[0], password)
    return False

def save_message(user, msg, type):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO messages (user,msg,type) VALUES (?,?,?)",(user,msg,type))
    conn.commit()
    msg_id = c.lastrowid
    conn.close()
    return msg_id

def update_last_seen(user):
    conn = connect()
    c = conn.cursor()
    c.execute("UPDATE users SET last_seen=? WHERE username=?",
    (datetime.now().strftime("%H:%M"), user))
    conn.commit()
    conn.close()

def set_status(user, status):
    conn = connect()
    c = conn.cursor()
    c.execute("UPDATE users SET status=? WHERE username=?",(status,user))
    conn.commit()
    conn.close()
