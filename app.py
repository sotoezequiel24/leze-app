import os
from flask import Flask, render_template, request, redirect, session, send_from_directory
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "leze_secret"
socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def db():
    return sqlite3.connect("chat.db")

def init():
    conn = db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password TEXT,
        status TEXT,
        last_seen TEXT
    )""")
    conn.commit()
    conn.close()

init()

def room(u1,u2):
    return "_".join(sorted([u1,u2]))

# LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]
        conn=db();c=conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p))
        if c.fetchone():
            session["user"]=u
            return redirect("/contacts")
    return render_template("login.html")

# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]
        conn=db();c=conn.cursor()
        try:
            c.execute("INSERT INTO users VALUES (?,?,?,?)",
            (u,p,"En línea 💚",str(datetime.now())))
            conn.commit()
            session["user"]=u
            return redirect("/contacts")
        except:
            pass
    return render_template("register.html")

# CONTACTOS
@app.route("/contacts")
def contacts():
    u=session.get("user")
    conn=db();c=conn.cursor()
    c.execute("SELECT username,status,last_seen FROM users WHERE username!=?",(u,))
    users=c.fetchall()
    return render_template("contacts.html",users=users,user=u)

# CHAT
@app.route("/chat/<other>")
def chat(other):
    return render_template("chat.html",user=session.get("user"),other=other)

# SUBIR ARCHIVOS
@app.route("/upload",methods=["POST"])
def upload():
    f=request.files["file"]
    name=secure_filename(f.filename)
    path=os.path.join(app.config["UPLOAD_FOLDER"],name)
    f.save(path)
    return {"url":"/uploads/"+name}

@app.route("/uploads/<f>")
def files(f):
    return send_from_directory(app.config["UPLOAD_FOLDER"],f)

# SOCKET
@socketio.on("join")
def join(data):
    join_room(room(data["user"],data["other"]))

@socketio.on("message")
def msg(data):
    data["status"]="✔"
    emit("message",data,room=room(data["user"],data["to"]))

@socketio.on("delivered")
def delivered(data):
    emit("delivered",data,room=room(data["user"],data["to"]))

@socketio.on("read")
def read(data):
    emit("read",data,room=room(data["user"],data["to"]))

@socketio.on("typing")
def typing(data):
    emit("typing",data["user"],room=room(data["user"],data["to"]))

@socketio.on("online")
def online(user):
    conn=db();c=conn.cursor()
    c.execute("UPDATE users SET status='En línea 💚' WHERE username=?",(user,))
    conn.commit()
    emit("status",{ "user":user,"status":"En línea 💚"},broadcast=True)

@socketio.on("offline")
def offline(user):
    now=str(datetime.now())
    conn=db();c=conn.cursor()
    c.execute("UPDATE users SET status='Desconectado 🤍', last_seen=? WHERE username=?",(now,user))
    conn.commit()

socketio.run(app,"0.0.0.0",port=int(os.environ.get("PORT",5000)))
