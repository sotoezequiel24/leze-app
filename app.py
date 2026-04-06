import os
from flask import Flask, render_template, request, redirect, session, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "leze_secret")
socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db.init_db()

users_online = set()

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        if db.check_user(user, pwd):
            session["user"] = user
            return redirect("/chat")

    return render_template("login.html")

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/")
    return render_template("chat.html", user=session["user"])

@app.route("/history")
def history():
    return {"messages": db.get_messages()}

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    filename = secure_filename(file.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)
    return {"url": f"/uploads/{filename}"}

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@socketio.on("connect")
def connect():
    user = session.get("user")
    if user:
        users_online.add(user)
        emit("online", list(users_online), broadcast=True)

@socketio.on("disconnect")
def disconnect():
    user = session.get("user")
    if user in users_online:
        users_online.remove(user)
        emit("online", list(users_online), broadcast=True)

@socketio.on("message")
def message(data):
    user = session.get("user")
    msg = data["msg"]

    db.save_message(user, msg)
    emit("message", {"user": user, "msg": msg}, broadcast=True)

@socketio.on("typing")
def typing():
    emit("typing", session.get("user"), broadcast=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
