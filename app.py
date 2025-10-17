from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
import os
from datetime import datetime

# === ENV ===
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable missing.")
client = OpenAI(api_key=api_key)

app = Flask(__name__)
app.secret_key = "supersecretkey"  # production'da değiştir
CORS(app)
bcrypt = Bcrypt(app)

# === DATABASE ===
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///syrixrm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    role = db.Column(db.String(10))  # user | assistant
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# === SYSTEM PROMPT ===
SYSTEM_PROMPT = """
You are SyrixRM, a refined AI assistant created by Relaquent.
Speak elegantly, give concise and intelligent answers.
"""

# === HTML PAGES ===

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SyrixRM | Login</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
* {box-sizing: border-box;}
body {
  margin: 0;
  height: 100vh;
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  display: flex; justify-content: center; align-items: center;
  font-family: 'Inter', sans-serif;
}
.card {
  background: rgba(255,255,255,0.15);
  padding: 40px;
  border-radius: 20px;
  backdrop-filter: blur(20px);
  color: white;
  text-align: center;
  width: 360px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.25);
  animation: fadeIn 0.8s ease;
}
.card h2 {
  font-size: 28px;
  margin-bottom: 20px;
}
input {
  width: 100%; padding: 12px; margin: 10px 0;
  border: none; border-radius: 10px;
  background: rgba(255,255,255,0.2);
  color: white; font-size: 14px;
}
input::placeholder {color: rgba(255,255,255,0.7);}
button {
  width: 100%; padding: 12px;
  background: white; color: #1e3c72;
  font-weight: 600; border: none; border-radius: 10px;
  cursor: pointer; transition: background 0.3s;
}
button:hover {
  background: #e0e0e0;
}
a {
  color: #fff; font-size: 14px; display: inline-block; margin-top: 10px;
  text-decoration: none; opacity: 0.8;
}
a:hover {opacity: 1;}
.guest-btn {
  margin-top: 15px;
  background: transparent;
  color: white;
  border: 1px solid white;
  transition: all 0.3s;
}
.guest-btn:hover {
  background: rgba(255,255,255,0.2);
}
@keyframes fadeIn {from {opacity: 0; transform: translateY(20px);} to {opacity: 1; transform: translateY(0);}}
</style>
</head>
<body>
<div class="card">
  <h2>Welcome to SyrixRM</h2>
  <form method="POST" action="/login">
    <input name="email" placeholder="Email" required>
    <input name="password" type="password" placeholder="Password" required>
    <button type="submit">Login</button>
  </form>
  <a href="/register">Create account</a>
  <form action="/guest" method="POST">
    <button class="guest-btn" type="submit">Continue as Guest</button>
  </form>
</div>
</body>
</html>
"""

REGISTER_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SyrixRM | Register</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
body {background: linear-gradient(135deg, #1e3c72, #2a5298); display: flex; justify-content: center; align-items: center; height: 100vh; font-family: 'Inter', sans-serif; margin:0;}
.card {background: rgba(255,255,255,0.15); padding: 40px; border-radius: 20px; backdrop-filter: blur(20px); color: white; text-align: center; width: 360px; box-shadow: 0 10px 40px rgba(0,0,0,0.25);}
input {width: 100%; padding: 12px; margin: 10px 0; border: none; border-radius: 10px; background: rgba(255,255,255,0.2); color: white;}
button {width: 100%; padding: 12px; background: white; color: #1e3c72; font-weight: 600; border: none; border-radius: 10px; cursor: pointer;}
button:hover {background: #e0e0e0;}
a {color: #fff; font-size: 14px; display: inline-block; margin-top: 10px;}
</style>
</head>
<body>
<div class="card">
  <h2>Create Account</h2>
  <form method="POST" action="/register">
    <input name="username" placeholder="Username" required>
    <input name="email" placeholder="Email" required>
    <input name="password" type="password" placeholder="Password" required>
    <button type="submit">Register</button>
  </form>
  <a href="/login">Back to login</a>
</div>
</body>
</html>
"""

CHAT_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SyrixRM</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root {--accent: #0058ff; --bg: #eef2f9; --chat-bg: rgba(255,255,255,0.6);}
body {background: var(--bg); font-family: 'Inter', sans-serif; display: flex; flex-direction: column; height: 100vh; margin: 0;}
header {display: flex; justify-content: space-between; align-items: center; padding: 16px 40px; background: rgba(255,255,255,0.6); backdrop-filter: blur(10px); box-shadow: 0 4px 15px rgba(0,0,0,0.1);}
.chat-container {flex: 1; display: flex; justify-content: center; align-items: center; padding: 20px;}
.chat-box {width: 75%; max-width: 900px; height: 80vh; background: var(--chat-bg); border-radius: 20px; display: flex; flex-direction: column; backdrop-filter: blur(15px); box-shadow: 0 10px 40px rgba(0,0,0,0.1);}
.messages {flex: 1; padding: 20px; overflow-y: auto;}
.msg {max-width: 70%; padding: 12px 16px; border-radius: 16px; margin: 6px 0; line-height: 1.5; animation: fadeIn 0.3s ease;}
.msg.user {align-self: flex-end; background: linear-gradient(120deg,#dfe9ff,#b9d4ff); color:#00358c;}
.msg.ai {align-self: flex-start; background: white; color:#222;}
.input-area {display: flex; padding: 12px; border-top: 1px solid rgba(0,0,0,0.05);}
.input-area input {flex: 1; padding: 10px; border: none; border-radius: 10px; outline: none;}
.input-area button {margin-left: 10px; padding: 10px 18px; background: var(--accent); color: white; border: none; border-radius: 10px; cursor:pointer;}
@keyframes fadeIn {from {opacity:0; transform: translateY(10px);} to {opacity:1; transform: translateY(0);}}
</style>
</head>
<body>
<header>
  <h2>SyrixRM</h2>
  <div>
    {% if username %}
      <span style="margin-right:10px;">👤 {{username}}</span>
      <a href="/logout" style="text-decoration:none; color:#0058ff;">Logout</a>
    {% else %}
      <a href="/login" style="text-decoration:none; color:#0058ff;">Login</a>
    {% endif %}
  </div>
</header>
<div class="chat-container">
  <div class="chat-box">
    <div class="messages" id="messages"></div>
    <div class="input-area">
      <input type="text" id="user-input" placeholder="Type a message..." onkeydown="if(event.key==='Enter')sendMessage()">
      <button onclick="sendMessage()">Send</button>
    </div>
  </div>
</div>
<script>
async function loadHistory(){
  const res = await fetch('/history');
  const data = await res.json();
  data.forEach(m=>appendMessage(m.content, m.role));
}
function appendMessage(text, role){
  const div = document.createElement('div');
  div.className = 'msg '+role;
  div.textContent = text;
  document.getElementById('messages').appendChild(div);
  div.scrollIntoView();
}
async function sendMessage(){
  const input = document.getElementById('user-input');
  const text = input.value.trim();
  if(!text) return;
  appendMessage(text,'user');
  input.value='';
  const res = await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});
  const data = await res.json();
  appendMessage(data.reply,'ai');
}
loadHistory();
</script>
</body>
</html>
"""

# === ROUTES ===

@app.route("/")
def root():
    return render_template_string(CHAT_PAGE, username=session.get("username"))

@app.route("/guest", methods=["POST"])
def guest():
    session.clear()
    return redirect(url_for('root'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        if User.query.filter((User.username == username) | (User.email == email)).first():
            return "Username or Email already taken."
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return REGISTER_PAGE

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for('root'))
        return "Invalid credentials."
    return LOGIN_PAGE

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/chat", methods=["POST"])
def chat():
    user_id = session.get("user_id")
    msg = request.json.get("message", "")

    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    if user_id:
        messages = Message.query.filter_by(user_id=user_id).order_by(Message.id.desc()).limit(10).all()
        for m in reversed(messages):
            history.append({"role": m.role, "content": m.content})
    history.append({"role": "user", "content": msg})

    response = client.chat.completions.create(model="gpt-4o-mini", messages=history)
    reply = response.choices[0].message.content

    if user_id:
        db.session.add(Message(user_id=user_id, role="user", content=msg))
        db.session.add(Message(user_id=user_id, role="assistant", content=reply))
        db.session.commit()

    return jsonify({"reply": reply})

@app.route("/history")
def history():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify([])
    messages = Message.query.filter_by(user_id=user_id).order_by(Message.id).all()
    return jsonify([{"role": m.role, "content": m.content} for m in messages])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
