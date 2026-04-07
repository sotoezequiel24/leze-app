from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, join_room, emit
import sqlite3, time, os

app = Flask(__name__)
app.secret_key = "secret"
socketio = SocketIO(app, async_mode="threading")

# ---------- DB ----------
def db():
    return sqlite3.connect("chat.db")

def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        msg TEXT,
        time REAL
    )""")

    conn.commit()
    conn.close()

init_db()

# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = db()
        c = conn.cursor()

        # Buscar usuario
        c.execute("SELECT * FROM users WHERE username=?", (u,))
        user = c.fetchone()

        if user:
            # Si existe, verificar contraseña
            if user[1] == p:
                session["user"] = u
                conn.close()
                return redirect("/contacts")
        else:
            # Si NO existe → lo crea
            c.execute("INSERT INTO users VALUES (?,?)", (u,p))
            conn.commit()
            session["user"] = u
            conn.close()
            return redirect("/contacts")

        conn.close()

    return render_template("login.html")
# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = db()
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?,?)",(u,p))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")

# ---------- CONTACTOS ----------
@app.route("/contacts")
def contacts():
    if "user" not in session:
        return redirect("/")

    user = session["user"]

    conn = db()
    c = conn.cursor()

    c.execute("SELECT username FROM users WHERE username != ?", (user,))
    users = c.fetchall()

    data = []

    for u in users:
        other = u[0]

        c.execute("""
        SELECT msg, time FROM messages
        WHERE (sender=? AND receiver=?)
        OR (sender=? AND receiver=?)
        ORDER BY time DESC LIMIT 1
        """,(user,other,other,user))

        last = c.fetchone()

        if last:
            msg, t = last
            time_str = time.strftime("%H:%M", time.localtime(t))
        else:
            msg = "Sin mensajes"
            time_str = ""

        data.append((other,msg,time_str))

    conn.close()

    return render_template("contacts.html", users=data, user=user)

# ---------- CHAT ----------
@app.route("/chat/<to_user>")
def chat(to_user):
    if "user" not in session:
        return redirect("/")

    user = session["user"]

    conn = db()
    c = conn.cursor()

    c.execute("""
    SELECT sender, msg FROM messages
    WHERE (sender=? AND receiver=?)
    OR (sender=? AND receiver=?)
    ORDER BY time
    """,(user,to_user,to_user,user))

    messages = c.fetchall()
    conn.close()

    return render_template("chat.html",
        user=user,
        to_user=to_user,
        messages=messages,
        room="_".join(sorted([user,to_user]))
    )

# ---------- AGREGAR CONTACTO ----------
@app.route("/add", methods=["GET","POST"])
def add_contact():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        username = request.form["username"]
        return redirect(f"/chat/{username}")

    return render_template("add.html")

# ---------- SOCKET ----------
@socketio.on("join")
def on_join(data):
    join_room(data["room"])

@socketio.on("message")
def handle_msg(data):
    conn = db()
    c = conn.cursor()

    c.execute("INSERT INTO messages (sender,receiver,msg,time) VALUES (?,?,?,?)",
              (data["user"], data["to"], data["msg"], time.time()))
    conn.commit()
    conn.close()

    emit("message", data, room=data["room"])

@socketio.on("typing")
def typing(data):
    emit("typing", data, room=data["room"], include_self=False)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
