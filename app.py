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
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")
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

# === LOGIN PAGE (light themed) ===
LOGIN_PAGE = """
<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SyrixRM • Giriş</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#f6f8fb;
  --card:#ffffff;
  --muted:#97a0b5;
  --accent-start:#5b8cff;
  --accent-end:#3db7ff;
  --glass: rgba(255,255,255,0.6);
}
*{box-sizing:border-box}
body{
  margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
  font-family:'Inter',sans-serif;background:linear-gradient(180deg,var(--bg),#ffffff);
}
.container{
  width:100%;max-width:920px;padding:40px;
  display:grid;grid-template-columns:1fr 420px;gap:30px;align-items:center;
}
.brand {
  padding:34px;border-radius:18px;background:linear-gradient(180deg,rgba(255,255,255,0.8),#ffffff);
  box-shadow:0 10px 40px rgba(60,80,120,0.06);border:1px solid rgba(14,30,60,0.04);
}
.logo {
  font-size:48px;font-weight:800; background: linear-gradient(90deg,var(--accent-start), var(--accent-end));
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.lead {margin-top:14px;color:var(--muted);font-size:15px}
.formcard {
  border-radius:18px;padding:28px;background:var(--card);
  box-shadow:0 12px 40px rgba(20,30,60,0.06);border:1px solid rgba(14,30,60,0.04);
}
.input{width:100%;padding:12px 14px;border-radius:12px;border:1px solid rgba(14,30,60,0.06);margin-top:12px;font-size:15px}
.btn {
  width:100%;padding:12px;border-radius:12px;border:none;margin-top:14px;
  background:linear-gradient(90deg,var(--accent-start), var(--accent-end));color:white;font-weight:600;
  box-shadow:0 8px 20px rgba(61,183,255,0.18);cursor:pointer;font-size:15px;
}
.ghost {background:transparent;border:1px solid rgba(14,30,60,0.06);color:var(--muted)}
.small {font-size:13px;color:var(--muted);margin-top:12px;display:block;text-align:center}
a {color:var(--accent-start);text-decoration:none;font-weight:600}
@media(max-width:880px){
  .container{grid-template-columns:1fr; padding:20px}
  .brand{order:2}
}
</style>
</head>
<body>
  <div class="container">
    <div class="brand">
      <div class="logo">SyrixRM</div>
      <div class="lead">Hassas, zarif ve özlü bir yapay zeka asistan. Hemen giriş yap veya misafir olarak devam et.</div>
    </div>
    <div class="formcard">
      <form method="POST" action="/login">
        <input class="input" name="email" placeholder="E-posta" required>
        <input class="input" name="password" type="password" placeholder="Parola" required>
        <button class="btn" type="submit">Giriş Yap</button>
      </form>
      <form method="POST" action="/guest" style="margin-top:8px">
        <button class="btn ghost" type="submit">Misafir Olarak Devam Et</button>
      </form>
      <div class="small">Hesabın yok mu? <a href="/register">Kayıt Ol</a></div>
    </div>
  </div>
</body>
</html>
"""

# === REGISTER PAGE (light themed) ===
REGISTER_PAGE = """
<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SyrixRM • Kayıt</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#f6f8fb;--card:#ffffff;--muted:#97a0b5;--accent-start:#5b8cff;--accent-end:#3db7ff;
}
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:'Inter',sans-serif;background:linear-gradient(180deg,var(--bg),#ffffff);}
.card{width:420px;padding:28px;border-radius:16px;background:var(--card);box-shadow:0 12px 40px rgba(20,30,60,0.06);border:1px solid rgba(14,30,60,0.04)}
h2{margin:0 0 8px 0;font-size:22px;background:linear-gradient(90deg,var(--accent-start), var(--accent-end));-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800}
.lead{color:var(--muted);font-size:14px;margin-bottom:18px}
.input{width:100%;padding:12px 14px;border-radius:12px;border:1px solid rgba(14,30,60,0.06);margin-top:10px;font-size:15px}
.btn{width:100%;padding:12px;border-radius:12px;border:none;margin-top:14px;background:linear-gradient(90deg,var(--accent-start), var(--accent-end));color:white;font-weight:600;box-shadow:0 8px 20px rgba(61,183,255,0.18);cursor:pointer}
.small{font-size:13px;color:var(--muted);margin-top:12px;text-align:center}
a{color:var(--accent-start);text-decoration:none;font-weight:600}
</style>
</head>
<body>
  <div class="card">
    <h2>Hesap Oluştur</h2>
    <div class="lead">SyrixRM ile hemen konuşmaya başla.</div>
    <form method="POST" action="/register">
      <input class="input" name="username" placeholder="Kullanıcı adı" required>
      <input class="input" name="email" placeholder="E-posta" required>
      <input class="input" name="password" type="password" placeholder="Parola" required>
      <button class="btn" type="submit">Kayıt Ol</button>
    </form>
    <div class="small">Zaten hesabın var mı? <a href="/login">Giriş Yap</a></div>
  </div>
</body>
</html>
"""

# === CHAT PAGE (light, premium, büyük chat alanı, typing effect) ===
CHAT_PAGE = """
<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SyrixRM</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#f7f9fc;
  --panel:#ffffff;
  --muted:#6b7280;
  --accent-start:#4f46e5; /* deep indigo */
  --accent-end:#06b6d4;   /* teal */
  --glass: rgba(255,255,255,0.75);
}
*{box-sizing:border-box}
html,body{height:100%;margin:0;font-family:'Inter',sans-serif;background:linear-gradient(180deg,var(--bg),#ffffff);color:#0f172a}
.app {
  min-height:100vh;display:flex;flex-direction:column;
}
.nav {
  display:flex;justify-content:space-between;align-items:center;padding:20px 36px;
  background:transparent;
}
.brand {font-weight:800;font-size:20px;
  background:linear-gradient(90deg,var(--accent-start),var(--accent-end));-webkit-background-clip:text;-webkit-text-fill-color:transparent;
}
.controls {display:flex;gap:12px;align-items:center}
.control-btn {padding:10px 12px;border-radius:10px;border:none;background:#fff;box-shadow:0 6px 18px rgba(12,24,50,0.06);cursor:pointer;font-weight:600}
.container {
  flex:1;display:flex;align-items:center;justify-content:center;padding:28px;
}
.panel {
  width:100%;max-width:1200px;height:80vh;border-radius:18px;
  background:linear-gradient(180deg,rgba(255,255,255,0.9),var(--panel));
  box-shadow:0 20px 60px rgba(15,23,42,0.08);display:grid;grid-template-columns:360px 1fr;overflow:hidden;border:1px solid rgba(10,20,40,0.04)
}

/* LEFT: side (conversations / actions) */
.side {
  padding:20px;border-right:1px solid rgba(10,20,40,0.04);background:linear-gradient(180deg,rgba(250,250,253,0.6),transparent);
}
.side .newconv {
  display:flex;gap:10px;margin-bottom:18px;
}
.newconv button{flex:1;padding:10px;border-radius:12px;border:none;background:linear-gradient(90deg,var(--accent-start),var(--accent-end));color:white;font-weight:700;cursor:pointer}
.side .meta {font-size:13px;color:var(--muted);margin-top:6px}

/* RIGHT: chat area */
.chat {
  padding:28px;display:flex;flex-direction:column;gap:12px;height:100%;background:transparent;
}
.header {
  display:flex;justify-content:space-between;align-items:center;padding-bottom:12px;border-bottom:1px solid rgba(10,20,40,0.03);
}
.h-title {font-weight:700;font-size:18px}
.h-sub {font-size:13px;color:var(--muted)}
.messages-wrap {
  flex:1;overflow:auto;padding:20px 12px;scrollbar-width:thin;
  display:flex;flex-direction:column;gap:16px;
  background:
    radial-gradient(600px 300px at 10% 10%, rgba(99,102,241,0.03), transparent 8%),
    radial-gradient(600px 300px at 90% 90%, rgba(6,182,212,0.02), transparent 8%);
  border-radius:12px;margin-top:12px;padding-bottom:30px;
}
.message {
  display:flex;gap:12px;align-items:flex-start;max-width:85%;
}
.message.user {margin-left:auto;flex-direction:row-reverse}
.avatar {
  width:44px;height:44px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:700;color:white;
  background:linear-gradient(135deg,var(--accent-start),var(--accent-end));box-shadow:0 6px 18px rgba(12,24,50,0.08);
}
.bubble {
  padding:14px 16px;border-radius:12px;background:linear-gradient(180deg,#ffffff,#fbfdff);box-shadow:0 10px 30px rgba(12,24,50,0.06);font-size:15px;line-height:1.45;border:1px solid rgba(10,20,40,0.04)
}
.user .bubble {background:linear-gradient(90deg,#eef2ff,#e0f7ff);border:1px solid rgba(59,130,246,0.12)}
.meta {font-size:12px;color:var(--muted);margin-top:6px}

/* input area (sticky bottom) */
.composer {
  display:flex;gap:12px;padding:18px;border-top:1px solid rgba(10,20,40,0.03);background:linear-gradient(180deg,transparent, rgba(255,255,255,0.6));
}
.textarea {
  flex:1;background:linear-gradient(180deg,#ffffff,#fbfbff);padding:14px;border-radius:12px;border:1px solid rgba(10,20,40,0.04);
  font-size:15px;resize:none;min-height:54px;max-height:220px;outline:none;box-shadow:0 6px 18px rgba(12,24,50,0.04);
}
.send {
  padding:12px 16px;border-radius:12px;border:none;background:linear-gradient(90deg,var(--accent-start),var(--accent-end));color:white;font-weight:700;cursor:pointer;
  box-shadow:0 8px 26px rgba(61,183,255,0.14)
}
.typing {
  display:flex;gap:6px;align-items:center;padding:8px 12px;border-radius:12px;background:rgba(15,23,42,0.02);font-size:13px;color:var(--muted);align-self:flex-start;
}
.dot {width:8px;height:8px;border-radius:50%;background:var(--muted);opacity:0.6}
.dot:nth-child(1){animation:jump 1s infinite;}
.dot:nth-child(2){animation:jump 1s 0.15s infinite;}
.dot:nth-child(3){animation:jump 1s 0.3s infinite;}
@keyframes jump{0%{transform:translateY(0)}50%{transform:translateY(-6px)}100%{transform:translateY(0)}}

/* scrollbar */
.messages-wrap::-webkit-scrollbar{width:10px}
.messages-wrap::-webkit-scrollbar-thumb{background:linear-gradient(180deg,rgba(100,116,139,0.16),rgba(100,116,139,0.08));border-radius:10px}

/* responsive */
@media(max-width:980px){
  .panel{grid-template-columns:1fr}
  .side{display:none}
  .container{padding:12px}
}
</style>
</head>
<body>
  <div class="app">
    <div class="nav">
      <div class="brand">SyrixRM</div>
      <div class="controls">
        {% if username %}
          <div style="font-weight:600;color:#0f172a">👤 {{username}}</div>
          <a href="/logout" class="control-btn">Çıkış</a>
        {% else %}
          <a href="/login" class="control-btn">Giriş</a>
        {% endif %}
      </div>
    </div>

    <div class="container">
      <div class="panel" role="main" aria-live="polite">
        <div class="side">
          <div class="newconv">
            <button onclick="newConversation()">+ Yeni Konuşma</button>
          </div>
          <div class="meta">Son konuşmalar otomatik kaydedilir.</div>
        </div>

        <div class="chat">
          <div class="header">
            <div>
              <div class="h-title">SyrixRM</div>
              <div class="h-sub">Zarif. Net. Yardımcı — Ne hakkında konuşmak istersiniz?</div>
            </div>
            <div id="typing-indicator" style="display:none" class="typing" aria-hidden="true">
              <div class="dot"></div><div class="dot"></div><div class="dot"></div>
              <div style="margin-left:8px;color:var(--muted);font-weight:600">yazıyor...</div>
            </div>
          </div>

          <div class="messages-wrap" id="messages"></div>

          <div class="composer">
            <textarea id="user-input" class="textarea" placeholder="Mesajınızı yazın... (Shift+Enter yeni satır)"></textarea>
            <button class="send" id="send-btn">Gönder</button>
          </div>
        </div>
      </div>
    </div>
  </div>

<script>
const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const typingIndicator = document.getElementById('typing-indicator');

function formatTime(dt){
  const d = new Date(dt);
  return d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
}

function appendMessage(text, role, meta=null, raw=false){
  const wrapper = document.createElement('div');
  wrapper.className = 'message ' + (role === 'user' ? 'user' : 'ai');

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = role === 'user' ? ({{ 'true' if session.get("username") else 'false' }} ? String("{{session.get('username') or 'U'}}").slice(0,2).toUpperCase() : 'U') : 'AI';

  const bubbleWrap = document.createElement('div');
  bubbleWrap.style.display = 'flex';
  bubbleWrap.style.flexDirection = 'column';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  if(raw){
    bubble.innerHTML = text;
  } else {
    bubble.textContent = text;
  }

  bubbleWrap.appendChild(bubble);

  if(meta){
    const m = document.createElement('div');
    m.className = 'meta';
    m.textContent = meta;
    bubbleWrap.appendChild(m);
  }

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubbleWrap);
  messagesEl.appendChild(wrapper);
  wrapper.scrollIntoView({behavior:'smooth', block:'end'});
  return bubble;
}

async function loadHistory(){
  const res = await fetch('/history');
  const data = await res.json();
  if(!data || data.length === 0){ 
    appendMessage("Merhaba! Sana nasıl yardım edebilirim?","ai", null);
    return;
  }
  data.forEach(m => {
    appendMessage(m.content, m.role, m.timestamp ? formatTime(m.timestamp) : null);
  });
}
function newConversation(){
  // basitçe temizle — sunucu tarafında yeni ID vs gerekirse ileride ekle
  messagesEl.innerHTML = '';
  appendMessage("Yeni konuşma başlatıldı. Nasıl yardımcı olabilirim?","ai");
}

function showTyping(on=true){
  typingIndicator.style.display = on ? 'flex' : 'none';
}

// typing effect: reveal characters gradually
function revealText(bubbleElem, text, speed=18){
  let i = 0;
  bubbleElem.textContent = '';
  return new Promise(resolve=>{
    const iv = setInterval(()=>{
      bubbleElem.textContent += text[i] === '\\n' ? '\\n' : text[i];
      i++;
      if(i >= text.length){
        clearInterval(iv);
        resolve();
      }
    }, speed);
  });
}

async function sendMessage(){
  const text = inputEl.value.trim();
  if(!text) return;
  // append user immediately
  appendMessage(text, 'user', formatTime(new Date()));
  inputEl.value = '';
  // show typing
  showTyping(true);
  // send to server
  try{
    const res = await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});
    if(!res.ok) throw new Error('Sunucu hatası');
    const data = await res.json();
    showTyping(false);

    // append empty bubble and reveal
    const bubble = appendMessage('', 'ai', formatTime(new Date()));
    await revealText(bubble, data.reply, 12); // karakter hızı (ms)
  } catch(err){
    showTyping(false);
    appendMessage('Üzgünüm, bir hata oluştu: ' + String(err),'ai');
  }
}

sendBtn.addEventListener('click', sendMessage);
inputEl.addEventListener('keydown', (e)=>{
  if(e.key === 'Enter' && !e.shiftKey){
    e.preventDefault();
    sendMessage();
  }
});

// Auto-resize textarea
inputEl.addEventListener('input', (e)=>{
  inputEl.style.height = 'auto';
  inputEl.style.height = (inputEl.scrollHeight) + 'px';
});

window.addEventListener('load', ()=>{
  loadHistory();
});
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
    # guest için username gösterilmesini istersen session["username"]="Guest" ekle
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
        messages = Message.query.filter_by(user_id=user_id).order_by(Message.id.desc()).limit(12).all()
        for m in reversed(messages):
            history.append({"role": m.role, "content": m.content})
    history.append({"role": "user", "content": msg})
    # OpenAI çağrısı
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
    # timestamp ISO string for client formatting
    return jsonify([{"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()} for m in messages])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
