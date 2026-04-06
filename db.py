import sqlite3

def connect():
    return sqlite3.connect("chat.db")

def init_db():
    conn = connect()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        msg TEXT
    )
    """)

    c.execute("INSERT OR IGNORE INTO users VALUES ('Leo','1234')")
    c.execute("INSERT OR IGNORE INTO users VALUES ('Eze','1234')")

    conn.commit()
    conn.close()

def check_user(user, pwd):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (user,pwd))
    result = c.fetchone()
    conn.close()
    return result

def save_message(user, msg):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO messages (user,msg) VALUES (?,?)",(user,msg))
    conn.commit()
    conn.close()

def get_messages():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT user, msg FROM messages")
    data = c.fetchall()
    conn.close()
    return data
