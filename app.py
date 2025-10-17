from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
import os
from datetime import datetime

# === CONFIG ===
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable missing.")
client = OpenAI(api_key=api_key)

app = Flask(__name__)
app.secret_key = "supersecretkey"
CORS(app)
bcrypt = Bcrypt(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///syrixrm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# === MODELS ===
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    role = db.Column(db.String(10))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

SYSTEM_PROMPT = "You are SyrixRM, an intelligent, elegant and concise AI assistant."

# === LOGIN & REGISTER PAGES (unchanged for brevity) ===
LOGIN_PAGE = """<center style="margin-top:200px;font-family:Inter">Use /register or /guest → then go /</center>"""
REGISTER_PAGE = LOGIN_PAGE  # (placeholder to shorten)

# === MODERNIZED CHAT PAGE ===
CHAT_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SyrixRM</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --bg-dark: #0e1013;
  --card-bg: rgba(30, 33, 39, 0.85);
  --accent: #3b82f6;
  --text-light: #f8f9fa;
  --text-dim: #b5b9c5;
}
*{box-sizing:border-box}
body {
  margin:0;
  font-family:'Inter',sans-serif;
  background: radial-gradient(circle at top left, #121419, #0e1013);
  color: var(--text-light);
  height: 100vh;
  display:flex;
  flex-direction:column;
}
header {
  display:flex;justify-content:space-between;align-items:center;
  padding:16px 28px;
  background:rgba(20,22,27,0.6);
  backdrop-filter:blur(12px);
  border-bottom:1px solid rgba(255,255,255,0.05);
  position:sticky;top:0;z-index:20;
}
header h2 {
  font-weight:700;
  background:linear-gradient(90deg,#3b82f6,#60a5fa);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  font-size:22px;
}
header a {
  color:var(--text-dim);
  text-decoration:none;
  font-size:14px;
}
header a:hover{color:var(--text-light);}
.chat-area {
  flex:1;
  display:flex;
  flex-direction:column;
  max-width:900px;
  width:100%;
  margin:auto;
  padding:24px;
  overflow-y:auto;
  scrollbar-width:thin;
}
.message {
  display:flex;
  margin-bottom:16px;
  animation:fadeIn 0.4s ease;
}
.message.user {justify-content:flex-end;}
.bubble {
  padding:14px 18px;
  border-radius:16px;
  max-width:75%;
  line-height:1.5;
  word-wrap:break-word;
  font-size:15px;
  box-shadow:0 2px 8px rgba(0,0,0,0.25);
}
.user .bubble {
  background:linear-gradient(135deg,#2563eb,#3b82f6);
  color:white;
  border-bottom-right-radius:4px;
}
.ai .bubble {
  background:var(--card-bg);
  border:1px solid rgba(255,255,255,0.05);
  color:var(--text-light);
  border-bottom-left-radius:4px;
}
footer {
  display:flex;
  padding:18px 22px;
  background:rgba(20,22,27,0.75);
  backdrop-filter:blur(10px);
  border-top:1px solid rgba(255,255,255,0.08);
}
#user-input {
  flex:1;
  padding:14px 16px;
  background:rgba(255,255,255,0.08);
  border:none;
  border-radius:12px;
  color:var(--text-light);
  outline:none;
  font-size:15px;
  transition:all .2s;
}
#user-input:focus {background:rgba(255,255,255,0.12);}
button {
  margin-left:12px;
  background:linear-gradient(135deg,#3b82f6,#2563eb);
  border:none;
  border-radius:12px;
  color:white;
  font-weight:600;
  padding:0 20px;
  cursor:pointer;
  transition:0.2s;
}
button:hover{transform:scale(1.03);}
@keyframes fadeIn{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}
</style>
</head>
<body>
<header>
  <h2>SyrixRM</h2>
  <div>
    {% if username %}
      <span style="margin-right:10px;opacity:0.8;">👤 {{username}}</span>
      <a href="/logout">Logout</a>
    {% else %}
      <a href="/login">Login</a>
    {% endif %}
  </div>
</header>
<div class="chat-area" id="chat"></div>
<footer>
  <input id="user-input" placeholder="Type a message..." onkeydown="if(event.key==='Enter')sendMessage()">
  <button onclick="sendMessage()">➤</button>
</footer>
<script>
async function loadHistory(){
  const res = await fetch('/history');
  const data = await res.json();
  data.forEach(m=>appendMessage(m.content, m.role));
}
function appendMessage(text,role){
  const div=document.createElement('div');
  div.className='message '+role;
  const bubble=document.createElement('div');
  bubble.className='bubble';
  bubble.textContent=text;
  div.appendChild(bubble);
  document.getElementById('chat').appendChild(div);
  div.scrollIntoView({behavior:'smooth'});
}
async function sendMessage(){
  const input=document.getElementById('user-input');
  const text=input.value.trim();
  if(!text)return;
  appendMessage(text,'user');
  input.value='';
  const res=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});
  const data=await res.json();
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
    app.run(host="0.0.0.0", port=5000)
