from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os

# === Render ortamı için API key kontrolü ===
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set in Render!")

client = OpenAI(api_key=api_key)
app = Flask(__name__)
CORS(app)

# === Hafıza ===
memory = []
SYSTEM_PROMPT = """
You are SyrixRM, an advanced conversational AI developed by Relaquent.
You are elegant, intelligent, and speak in a refined yet friendly tone.
Keep your responses insightful, concise, and premium in style.
"""

# === HTML SAYFASI ===
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SyrixRM | Relaquent</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --accent: #0058ff;
  --accent-light: #4f9cff;
  --bg-gradient: linear-gradient(135deg, #0f172a, #1e3a8a);
  --glass: rgba(255,255,255,0.07);
  --border: rgba(255,255,255,0.12);
  --text: #ffffff;
  --muted: #9ca3af;
}
*{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif;}
body{height:100vh;display:flex;flex-direction:column;background:var(--bg-gradient);color:var(--text);overflow:hidden;}
body::before{content:'';position:fixed;width:100%;height:100%;background:radial-gradient(circle at 30% 40%,rgba(79,156,255,0.15),transparent 60%),radial-gradient(circle at 70% 70%,rgba(0,88,255,0.1),transparent 60%);animation:glowMove 14s ease-in-out infinite alternate;z-index:-1;}
@keyframes glowMove{from{transform:scale(1);}to{transform:scale(1.05) translateY(-20px);}}
header{display:flex;justify-content:space-between;align-items:center;padding:26px 60px;background:rgba(255,255,255,0.05);backdrop-filter:blur(16px);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:10;}
.logo h1{font-size:28px;background:linear-gradient(90deg,#4f9cff,#0058ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.logo p{font-size:13px;color:var(--muted);font-style:italic;}
main{flex:1;display:flex;justify-content:center;align-items:center;padding:40px;}
.chat-container{width:75%;max-width:900px;height:80vh;background:var(--glass);border:1px solid var(--border);border-radius:24px;backdrop-filter:blur(30px);box-shadow:0 0 30px rgba(0,0,0,0.3);display:flex;flex-direction:column;overflow:hidden;}
.chat-header{padding:16px 24px;border-bottom:1px solid var(--border);font-weight:600;background:rgba(255,255,255,0.05);}
.chat-box{flex:1;padding:20px 28px;overflow-y:auto;display:flex;flex-direction:column;scroll-behavior:smooth;}
.msg{max-width:75%;padding:14px 18px;border-radius:16px;margin:8px 0;line-height:1.6;font-size:15px;animation:floatMsg 0.5s ease both;}
@keyframes floatMsg{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}
.user{align-self:flex-end;background:linear-gradient(120deg,#4f9cff,#0058ff);color:white;box-shadow:0 4px 14px rgba(79,156,255,0.25);}
.ai{align-self:flex-start;background:rgba(255,255,255,0.08);color:#f1f5f9;border:1px solid var(--border);}
#typing{display:none;font-size:13px;color:var(--muted);margin:6px 0;text-align:left;animation:blink 1.2s infinite;}
@keyframes blink{0%,100%{opacity:0.4;}50%{opacity:1;}}
.input-area{display:flex;padding:14px;border-top:1px solid var(--border);background:rgba(255,255,255,0.04);}
.input-area input{flex:1;border:none;outline:none;padding:12px 16px;border-radius:10px;background:rgba(255,255,255,0.1);color:white;font-size:15px;transition:0.3s;}
.input-area input:focus{background:rgba(255,255,255,0.2);}
.input-area button{margin-left:10px;border:none;border-radius:10px;padding:12px 22px;font-weight:600;background:linear-gradient(90deg,var(--accent),var(--accent-light));color:white;cursor:pointer;transition:0.3s;box-shadow:0 0 15px rgba(79,156,255,0.3);}
.input-area button:hover{transform:translateY(-1px);box-shadow:0 0 20px rgba(79,156,255,0.45);}
footer{text-align:center;padding:18px;font-size:13px;color:var(--muted);background:rgba(255,255,255,0.05);border-top:1px solid var(--border);}
</style>
</head>
<body>
<header>
  <div class="logo"><h1>SyrixRM</h1><p>by Relaquent</p></div>
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
<script>
const chatBox=document.getElementById('chat-box');
const input=document.getElementById('user-input');
const typing=document.getElementById('typing');
async function sendMessage(){
  const text=input.value.trim();
  if(!text) return;
  appendMessage(text,'user');
  input.value='';
  showTyping(true);
  const res=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});
  const data=await res.json();
  showTyping(false);
  typeWriter(data.reply,'ai');
}
function appendMessage(text,sender){
  const div=document.createElement('div');
  div.className='msg '+sender;
  div.textContent=text;
  chatBox.appendChild(div);
  chatBox.scrollTop=chatBox.scrollHeight;
}
function showTyping(state){
  typing.style.display=state?'block':'none';
  chatBox.scrollTop=chatBox.scrollHeight;
}
function typeWriter(text,sender){
  const div=document.createElement('div');
  div.className='msg '+sender;
  chatBox.appendChild(div);
  let i=0;
  const interval=setInterval(()=>{
    div.textContent=text.substring(0,i++);
    chatBox.scrollTop=chatBox.scrollHeight;
    if(i>text.length)clearInterval(interval);
  },15);
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
    user_msg = request.json.get("message", "")
    memory.append({"role": "user", "content": user_msg})
    conversation = [{"role": "system", "content": SYSTEM_PROMPT}] + memory[-10:]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation
    )
    reply = response.choices[0].message.content
    memory.append({"role": "assistant", "content": reply})
    return jsonify({"reply": reply})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render otomatik port verir
    app.run(host="0.0.0.0", port=port)
