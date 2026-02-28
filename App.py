from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import bcrypt
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Database Setup
def init_db():
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password BLOB
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        message TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    if "user" in session:
        return redirect("/chat")
    return redirect("/login")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = bcrypt.hashpw(request.form["password"].encode(), bcrypt.gensalt())

        conn = sqlite3.connect("chat.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)",
                      (name,email,password))
            conn.commit()
            conn.close()
            return redirect("/login")
        except:
            conn.close()
            return "Email already exists"

    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("chat.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode(), user[3]):
            session["user"] = user[1]
            return redirect("/chat")
        else:
            return "Invalid credentials"

    return render_template("login.html")

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/login")
    return render_template("chat.html", user=session["user"])

@app.route("/send", methods=["POST"])
def send():
    message = request.json["message"]

    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("INSERT INTO messages (user,message,timestamp) VALUES (?,?,?)",
              (session["user"], message, datetime.now()))
    conn.commit()
    conn.close()

    return jsonify({"status":"ok"})

@app.route("/messages")
def messages():
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 50")
    msgs = c.fetchall()
    conn.close()

    data = []
    for m in msgs[::-1]:
        data.append({"user":m[1], "message":m[2], "time":m[3]})

    return jsonify(data)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
