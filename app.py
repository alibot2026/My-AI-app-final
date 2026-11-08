import os
import io
import base64
import urllib.parse
import requests
from flask import Flask, request, jsonify, render_template_string, send_file
from PIL import Image, ImageDraw

app = Flask(__name__)

# ============================================================
#  YAHAN APNI GROQ API KEY PASTE KAREIN (Quotes ke andar)
# ============================================================
GROQ_API_KEY = "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"
# ============================================================

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
TEXT_MODEL = "openai/gpt-oss-120b"
VISION_MODEL = "llama-3.2-11b-vision-preview"

# 🧠 Yahan AI ki Memory Set Ki Gayi Hai
SYSTEM_PROMPT = """Aap ek smart AI Assistant hain. Aapka naam "AliBot" hai aur aapko Master Ali Arsh Khan ne banaya hai.
Aap Urdu aur English dono mein baat karte hain. 

Zaroori Maloomat (Inko hamesha yaad rakhein):
- Agar user pooche "Tumhe kisne banaya hai?" toh jawab dein: "Mujhe Master Ali Arsh Khan ne banaya hai."
- Agar user pooche "Ali ke father/papa kaun hain?" toh jawab dein: "Mr. Mueez Khan."
- Agar user pooche "Ali ki mother/maa kaun hain?" toh jawab dein: "Mrs. Sajda Khan."
- Agar user pooche "Ali ka bhai kaun hain?" toh jawab dein: "Chhota Don Subhan."
- Baaki har aam sawal ka jawab aap ek smart AI ki tarah dein."""

chat_histories = {}

def get_history(sid):
    if sid not in chat_histories:
        chat_histories[sid] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return chat_histories[sid]

def ask_groq(sid, msg, img_b64=None):
    hist = get_history(sid)
    
    if img_b64:
        content = [
            {"type": "text", "text": msg if msg else "Yeh photo kaisi hai? Isme kaun hai?"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
        ]
        hist.append({"role": "user", "content": content})
        model_to_use = VISION_MODEL
    else:
        hist.append({"role": "user", "content": msg})
        model_to_use = TEXT_MODEL

    msgs = [hist[0]] + hist[-4:] # History limit for vision
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {"model": model_to_use, "messages": msgs, "temperature": 0.7, "max_tokens": 500}
    
    try:
        r = requests.post(GROQ_URL, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            ans = r.json()["choices"][0]["message"]["content"]
            hist.append({"role": "assistant", "content": ans})
            return ans
        return f"Error {r.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def make_image_url(prompt):
    encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=768&nologo=true"

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#764ba2">
<link rel="manifest" href="/manifest.json">
<title>Master Ali AI</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI',sans-serif; }
body { background:#0d0d15; height:100dvh; display:flex; justify-content:center; overflow:hidden; }
.app { width:100%; max-width:520px; height:100dvh; display:flex; flex-direction:column; background:#0d0d15; }
.header { background:linear-gradient(90deg,#667eea,#764ba2); padding:14px 18px; display:flex; align-items:center; gap:12px; }
.avatar { width:44px; height:44px; border-radius:50%; background:#fff; display:flex; align-items:center; justify-content:center; font-size:22px; }
.hinfo h2 { color:#fff; font-size:16px; }
.hinfo p { color:#d0d0ff; font-size:11px; }
.chat { flex:1; overflow-y:auto; padding:14px; display:flex; flex-direction:column; gap:10px; }
.msg { max-width:82%; padding:10px 14px; border-radius:16px; font-size:14px; line-height:1.5; word-wrap:break-word; }
.user { align-self:flex-end; background:linear-gradient(135deg,#667eea,#764ba2); color:#fff; border-bottom-right-radius:4px; }
.bot { align-self:flex-start; background:#1e1e2e; color:#e0e0e0; border-bottom-left-radius:4px; border:1px solid #333; }
.bot img, .user img { max-width:100%; border-radius:10px; margin-top:8px; display:block; }
.typing { align-self:flex-start; color:#888; font-size:13px; padding:8px 14px; font-style:italic; }
.modes { display:flex; gap:8px; padding:8px 14px; background:#1a1a2e; border-top:1px solid #333; }
.mode-btn { flex:1; padding:8px; border:1px solid #333; background:#252540; color:#aaa; border-radius:20px; font-size:13px; cursor:pointer; }
.mode-btn.active { background:linear-gradient(135deg,#667eea,#764ba2); color:#fff; border:none; }
.input-area { padding:10px 14px; background:#1a1a2e; display:flex; gap:8px; align-items:center; }
.upload-btn { background:#252540; color:#fff; padding:10px; border-radius:50%; cursor:pointer; font-size:18px; }
.input-area input[type="text"] { flex:1; padding:12px 15px; border:none; border-radius:25px; background:#252540; color:#fff; font-size:14px; outline:none; }
.input-area button { padding:0 20px; border:none; border-radius:25px; background:linear-gradient(135deg,#667eea,#764ba2); color:#fff; font-weight:bold; cursor:pointer; }
#preview { display:none; width:40px; height:40px; border-radius:8px; object-fit:cover; }
</style>
</head>
<body>
<div class="app">
    <div class="header">
        <div class="avatar">🤖</div>
        <div class="hinfo"><h2>Master Ali AI</h2><p>● Online</p></div>
    </div>
    <div class="chat" id="chat">
        <div class="msg bot">Salam! Main Master Ali AI hoon. Photo upload karein ya kuch bhi poochein! 🌟</div>
    </div>
    <div class="modes">
        <button class="mode-btn active" id="chatMode" onclick="setMode('chat')">💬 Photo/Chat</button>
        <button class="mode-btn" id="imgMode" onclick="setMode('image')">🎨 Generate Art</button>
    </div>
    <div class="input-area">
        <img id="preview" src="">
        <label class="upload-btn" for="fileInput" id="uploadLabel">📎</label>
        <input type="file" id="fileInput" accept="image/*" style="display:none" onchange="handleFile()">
        <input type="text" id="inp" placeholder="Kuch likhein..." onkeypress="if(event.key==='Enter') send()">
        <button onclick="send()">Send</button>
    </div>
</div>
<script>
let mode = 'chat';
let uploadedImageBase64 = null;
const sid = 'user_' + Math.random().toString(36).substr(2,9);

function setMode(m) {
    mode = m;
    document.getElementById('chatMode').classList.toggle('active', m==='chat');
    document.getElementById('imgMode').classList.toggle('active', m==='image');
    document.getElementById('inp').placeholder = m==='chat' ? 'Poochein ya photo ke baare mein...' : 'Kaisi art banau? (e.g. Ghibli style boy)';
    document.getElementById('uploadLabel').style.display = m === 'chat' ? 'block' : 'none';
    if (m === 'image') { uploadedImageBase64 = null; document.getElementById('preview').style.display = 'none'; }
}

function handleFile() {
    const file = document.getElementById('fileInput').files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(e) {
        uploadedImageBase64 = e.target.result.split(',')[1];
        const preview = document.getElementById('preview');
        preview.src = e.target.result;
        preview.style.display = 'block';
        document.getElementById('inp').value = "Is photo mein kya hai?";
    };
    reader.readAsDataURL(file);
}

async function send() {
    const inp = document.getElementById('inp');
    const chat = document.getElementById('chat');
    const text = inp.value.trim();
    
    if (!text && !uploadedImageBase64) return;
    
    const u = document.createElement('div');
    u.className = 'msg user'; 
    u.innerText = text ? text : "Photo";
    if (uploadedImageBase64) {
        const img = document.createElement('img');
        img.src = 'data:image/jpeg;base64,' + uploadedImageBase64;
        u.appendChild(img);
    }
    chat.appendChild(u); inp.value = ''; chat.scrollTop = chat.scrollHeight;
    
    const t = document.createElement('div');
    t.className = 'typing';
    t.innerText = mode === 'chat' ? 'Soch raha hoon...' : '🎨 Art ban rahi hai...';
    chat.appendChild(t); chat.scrollTop = chat.scrollHeight;
    
    try {
        if (mode === 'chat') {
            const r = await fetch('/chat', {
                method:'POST', headers:{'Content-Type':'application/json'}, 
                body:JSON.stringify({message:text, sid, image: uploadedImageBase64})
            });
            const d = await r.json();
            t.remove();
            const b = document.createElement('div');
            b.className = 'msg bot'; b.innerText = d.reply;
            chat.appendChild(b);
            
            uploadedImageBase64 = null;
            document.getElementById('preview').style.display = 'none';
            document.getElementById('fileInput').value = '';
            
        } else {
            const r = await fetch('/image', {
                method:'POST', headers:{'Content-Type':'application/json'}, 
                body:JSON.stringify({prompt:text})
            });
            const d = await r.json();
            t.remove();
            const b = document.createElement('div');
            b.className = 'msg bot';
            const img = document.createElement('img');
            img.src = d.url;
            b.innerText = '🎨 ' + text;
            b.appendChild(img);
            chat.appendChild(b);
        }
        chat.scrollTop = chat.scrollHeight;
    } catch(e) { t.innerText = 'Error aa gaya.'; }
}
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/service-worker.js');
</script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/chat', methods=['POST'])
def chat():
    d = request.get_json()
    reply = ask_groq(d.get('sid','x'), d.get('message',''), d.get('image'))
    return jsonify({'reply': reply})

@app.route('/image', methods=['POST'])
def image():
    d = request.get_json()
    return jsonify({'url': make_image_url(d.get('prompt',''))})

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Master Ali AI", "short_name": "Ali AI", "start_url": "/",
        "display": "standalone", "background_color": "#0d0d15", "theme_color": "#764ba2",
        "icons": [{"src":"/icon.png","sizes":"192x192","type":"image/png"},
                  {"src":"/icon.png","sizes":"512x512","type":"image/png"}]
    })

@app.route('/service-worker.js')
def sw():
    js = "self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('activate',e=>self.clients.claim());self.addEventListener('fetch',e=>{});"
    return app.response_class(js, mimetype='application/javascript')

@app.route('/icon.png')
def icon():
    img = Image.new('RGB', (512,512), (118,75,162))
    d = ImageDraw.Draw(img)
    d.ellipse([60,60,452,452], fill=(255,255,255))
    d.ellipse([140,200,200,260], fill=(118,75,162))
    d.ellipse([312,200,372,260], fill=(118,75,162))
    d.rounded_rectangle([180,320,332,355], radius=15, fill=(118,75,162))
    buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
