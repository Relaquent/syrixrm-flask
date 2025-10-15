from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os

# === CONFIG ===
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

client = OpenAI(api_key=api_key)
app = Flask(__name__)
CORS(app)

# === MEMORY ===
syrix_memory = []
SYRIX_SYSTEM_PROMPT = """
You are SyrixRM, an advanced conversational AI developed by Relaquent.
You are elegant, intelligent, and speak in a refined yet friendly tone.
Keep your responses insightful, concise, and premium in style.
"""

# === FRONTEND ===
HTML_PAGE = """ 
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SyrixRM | Relaquent</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
body{margin:0;font-family:'Inter',sans-serif;background:linear-gradient(135deg,#eef2f9,#dfe6f3);
color:#1a1a1a;display:flex;flex-direction:column;min-height:100vh;overflow:hidden;}
#intro{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,0.8);
backdrop-filter:blur(20px);animation:introFade 3s ease forwards;z-index:50;}
#intro-content{text-align:center;animation:logoFade 2.5s ease forwards;}
#intro h1{font-size:46px;background:linear-gradient(90deg,#0058ff,#4f9cff);
-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;}
#intro p{color:#707070;}
@keyframes logoFade{0%{opacity:0;transform:scale(.9);}25%{opacity:1;transform:scale(1);}80%{opacity:1;}100%{opacity:0;transform:scale(1.05);}}
@keyframes introFade{0%,85%{opacity:1;}100%{opacity:0;visibility:hidden;}}
header{margin-top:60px;text-align:center;}
h1{font-size:42px;background:linear-gradient(90deg,#0058ff,#4f9cff);
-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:6px;}
.chat{width:80%;max-width:700px;margin:auto;margin-top:40px;background:rgba(255,255,255,0.8);
backdrop-filter:blur(12px);border-radius:20px;box-shadow:0 8px 35px rgba(0,0,0,0.08);display:flex;flex-direction:column;overflow:hidden;}
.messages{flex:1;padding:20px;overflow-y:auto;display:flex;flex-direction:column;}
.msg{margin:6px 0;padding:12px 16px;border-radius:14px;max-width:70%;animation:pop .4s ease;}
.user{align-self:flex-end;background:#e8f0ff;color:#00358c;}
.ai{align-self:flex-start;background:#f5f6f8;}
.input{display:flex;border-top:1px solid #ddd;background:rgba(255,255,255,0.6);}
input{flex:1;padding:14px;border:none;outline:none;background:transparent;}
button{background:linear-gradient(90deg,#0058ff,#4f9cff);color:white;border:none;padding:14px 20px;cursor:pointer;font-weight:600;}
button:hover{opacity:.9;}
footer{margin:40px 0 20px;color:#999;font-size:14px;text-align:center;}
@keyframes pop{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}
</style>
</head>
<body>
<div id="intro"><div id="intro-content"><h1>SyrixRM</h1><p>by Relaquent</p></div></div>
<header><h1>SyrixRM</h1><p>by Relaquent</p></header>
<div class="chat">
  <div class="messages" id="chat-box"></div>
  <div class="input">
    <input id="user-input" placeholder="Type a message..." onkeydown="if(event.key==='Enter')sendMessage()">
    <button onclick="sendMessage()">Send</button>
  </div>
</div>
<footer>© 2025 Relaquent — Elegant Intelligence.</footer>
<script>
const chatBox=document.getElementById('chat-box');
async function sendMessage(){
  const input=document.getElementById('user-input');
  const text=input.value.trim(); if(!text)return;
  append(text,'user'); input.value='';
  const res=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});
  const data=await res.json(); append(data.reply,'ai');
}
function append(t,cls){const d=document.createElement('div');d.className='msg '+cls;d.textContent=t;
chatBox.appendChild(d);chatBox.scrollTop=chatBox.scrollHeight;}
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
