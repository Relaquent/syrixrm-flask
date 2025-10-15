from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os

# === ENV SETUP ===
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

client = OpenAI(api_key=api_key)
app = Flask(__name__)
CORS(app)

# === SyrixRM MEMORY ===
syrix_memory = []
SYRIX_SYSTEM_PROMPT = """
You are SyrixRM, an advanced conversational AI developed by Relaquent.
You are elegant, intelligent, and speak in a refined yet friendly tone.
Keep your responses insightful, concise, and premium in style.
"""

# === FRONTEND HTML ===
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SyrixRM | Relaquent</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
/* === CSS aynı senin kodun === */
:root {
  --accent: #0058ff;
  --accent-light: #4f9cff;
  --bg: #eef2f9;
  --text: #1a1a1a;
  --muted: #707070;
  --chat-bg: rgba(255,255,255,0.7);
}
* {margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', sans-serif;}
body {background: var(--bg); color: var(--text); height: 100vh; display: flex; flex-direction: column; overflow: hidden;}
body::before {content: ''; position: fixed; width: 100%; height: 100%;
background: radial-gradient(circle at 30% 30%, rgba(0,88,255,0.08), transparent 60%),
            radial-gradient(circle at 70% 70%, rgba(79,156,255,0.08), transparent 60%);
z-index: -1; animation: floatBackground 12s ease-in-out infinite alternate;}
@keyframes floatBackground {from {transform: scale(1) translateY(0);} to {transform: scale(1.05) translateY(-20px);}}
#intro {position: fixed; top: 0; left: 0; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; background: rgba(255,255,255,0.8); backdrop-filter: blur(20px); z-index: 50; animation: introFade 3.2s ease forwards;}
#intro-content {text-align: center; animation: logoFade 2.8s ease-in-out forwards;}
#intro h1 {font-size: 46px; font-weight: 700; background: linear-gradient(90deg, var(--accent), var(--accent-light)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
#intro p {font-size: 15px; color: var(--muted); letter-spacing: 1px;}
@keyframes logoFade {0% {opacity: 0; transform: scale(0.9);} 25% {opacity: 1; transform: scale(1);} 80% {opacity: 1;} 100% {opacity: 0; transform: scale(1.05);}}
@keyframes introFade {0% {opacity: 1;} 85% {opacity: 1;} 100% {opacity: 0; visibility: hidden;}}
header {display: flex; justify-content: space-between; align-items: center; padding: 28px 60px; background: rgba(255,255,255,0.45); backdrop-filter: blur(20px); box-shadow: 0 8px 30px rgba(0,0,0,0.06); position: sticky; top: 0; z-index: 10;}
.logo h1 {font-weight: 700; font-size: 28px; background: linear-gradient(90deg, var(--accent), var(--accent-light)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 3px;}
.logo p {font-size: 13px; color: var(--muted); font-style: italic;}
nav {display: flex; gap: 24px;}
nav button {background: none; border: none; font-weight: 500; font-size: 15px; cursor: pointer; color: var(--text); transition: 0.3s; position: relative;}
nav button::after {content: ''; position: absolute; bottom: -2px; left: 0; width: 0%; height: 2px; background: var(--accent); transition: width 0.3s ease;}
nav button:hover {color: var(--accent);}
nav button:hover::after {width: 100%;}
main {flex: 1; display: flex; justify-content: center; align-items: center; padding: 40px; opacity: 0; animation: mainFade 3.2s ease forwards; animation-delay: 2.5s;}
@keyframes mainFade {to {opacity: 1;}}
.chat-container {width: 75%; max-width: 900px; height: 80vh; background: var(--chat-bg); border-radius: 24px; box-shadow: 0 15px 45px rgba(0,0,0,0.12); backdrop-filter: blur(22px); display: flex; flex-direction: column; overflow: hidden;}
.chat-header {padding: 16px 24px; border-bottom: 1px solid rgba(255,255,255,0.3); font-weight: 600; font-size: 16px; background: linear-gradient(90deg, rgba(255,255,255,0.3), rgba(255,255,255,0.1)); text-shadow: 0 0 10px rgba(255,255,255,0.3);}
.chat-box {flex: 1; padding: 20px 28px; overflow-y: auto; display: flex; flex-direction: column; scroll-behavior: smooth;}
.msg {max-width: 75%; padding: 14px 18px; border-radius: 18px; margin: 8px 0; line-height: 1.6; font-size: 15px;}
.user {align-self: flex-end; background: linear-gradient(120deg, #dfe9ff, #b9d4ff); color: #00358c;}
.ai {align-self: flex-start; background: rgba(255,255,255,0.65); color: #202020;}
#typing {display: none; font-size: 13px; color: var(--muted); margin: 6px 0; text-align: left;}
.input-area {display: flex; border-top: 1px solid rgba(255,255,255,0.3); padding: 14px; background: rgba(255,255,255,0.4); backdrop-filter: blur(10px);}
.input-area input {flex: 1; border: none; outline: none; padding: 12px 16px; border-radius: 10px; background: rgba(255,255,255,0.8); font-size: 15px;}
.input-area button {margin-left: 10px; border: none; border-radius: 10px; padding: 12px 22px; font-weight: 600; background: linear-gradient(90deg,var(--accent),var(--accent-light)); color: white; cursor: pointer;}
footer {text-align: center; padding: 18px; font-size: 14px; color: var(--muted); background: rgba(255,255,255,0.6);}
.modal {display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.4); backdrop-filter: blur(8px); justify-content: center; align-items: center; z-index: 20;}
.modal-content {background: white; width: 420px; padding: 28px; border-radius: 18px; text-align: center;}
</style>
</head>
<body>

<div id="intro"><div id="intro-content"><h1>SyrixRM</h1><p>by Relaquent</p></div></div>

<header>
  <div class="logo"><h1>SyrixRM</h1><p>by Relaquent</p></div>
  <nav>
    <button onclick="openModal('about')">About</button>
    <button onclick="openModal('projects')">Projects</button>
  </nav>
</header>

<main>
  <div class="chat-container">
    <div class="chat-header">SyrixRM</div>
    <div class="chat-box" id="chat-box"></div>
    <div id="typing">SyrixRM is typing...</div>
    <div class="input-area">
      <input type="text" id="user-input" placeholder="Type a message..." onkeydown="if(event.key==='Enter') sendMessage()">
      <button onclick="sendMessage()">Send</button>
    </div>
  </div>
</main>

<footer>© 2025 Relaquent — Built with precision and passion.</footer>

<div class="modal" id="about-modal">
  <div class="modal-content">
    <h2>About Relaquent</h2>
    <p>Relaquent merges creativity, intelligence, and technology to craft premium AI experiences.</p>
    <button onclick="closeModal('about')">Close</button>
  </div>
</div>

<div class="modal" id="projects-modal">
  <div class="modal-content">
    <h2>Projects</h2>
    <p>• ReTrace OSINT<br>• Auralink AI<br>• Vynex Tools</p>
    <button onclick="closeModal('projects')">Close</button>
  </div>
</div>

<script>
const chatBox = document.getElementById('chat-box');
const input = document.getElementById('user-input');
const typing = document.getElementById('typing');

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  appendMessage(text, 'user');
  input.value = '';
  showTyping(true);

  const res = await fetch('/chat', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ message: text })
  });

  const data = await res.json();
  showTyping(false);
  typeWriter(data.reply, 'ai');
}

function appendMessage(text, sender) {
  const div = document.createElement('div');
  div.className = 'msg ' + sender;
  div.textContent = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function showTyping(state) {
  typing.style.display = state ? 'block' : 'none';
  chatBox.scrollTop = chatBox.scrollHeight;
}

function typeWriter(text, sender) {
  const div = document.createElement('div');
  div.className = 'msg ' + sender;
  chatBox.appendChild(div);
  let i = 0;
  const interval = setInterval(() => {
    div.textContent = text.substring(0, i++);
    chatBox.scrollTop = chatBox.scrollHeight;
    if (i > text.length) clearInterval(interval);
  }, 15);
}

function openModal(name) {
  document.getElementById(name+'-modal').style.display = 'flex';
}
function closeModal(name) {
  document.getElementById(name+'-modal').style.display = 'none';
}
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    syrix_memory.append({"role": "user", "content": user_message})
    conversation = [{"role": "system", "content": SYRIX_SYSTEM_PROMPT}] + syrix_memory[-10:]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation
    )
    reply = response.choices[0].message.content
    syrix_memory.append({"role": "assistant", "content": reply})
    return jsonify({"reply": reply})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
