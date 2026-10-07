import os
import traceback
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)

# Read the API key from Render's Environment Variables.
raw_key = os.environ.get("GEMINI_API_KEY") or ""
GEMINI_API_KEY = raw_key.strip().strip('"').strip("'").strip()

# Models to try, in order. The FIRST one is used most, so it is the
# fastest one. If it is busy, the server tries the next one.
MODELS = [
    "gemini-3.5-flash-lite",   # fastest
    "gemini-3.8-flash",        # smartest
    "gemini-3.7-flash",        # backup
]

# How long to wait for Google on each try, in milliseconds (12 seconds).
GEMINI_TIMEOUT_MS = 12000

# Tells JARVIS how to talk. Short answers = faster and nicer to listen to.
SYSTEM_PROMPT = (
    "You are JARVIS, a friendly voice assistant. "
    "Reply in 1 to 3 short sentences. Use plain words only: "
    "no markdown, no lists, no emojis, no asterisks. "
    "Reply in the same language the user speaks."
)

client = None
if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
    )
    print("Gemini client created.", flush=True)
else:
    print("WARNING: GEMINI_API_KEY is not set. /chat will return an error.", flush=True)


# ---------------------------------------------------------------
# The phone page (voice in, voice out). Open it at /app
# ---------------------------------------------------------------
PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0b1220">
<title>JARVIS</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; background: #0b1220; color: #e6edf7;
    font-family: system-ui, Arial, sans-serif;
    display: flex; flex-direction: column; height: 100vh; height: 100dvh;
  }
  header { padding: 14px 16px; text-align: center; font-size: 20px;
           letter-spacing: 4px; color: #4cc9f0; border-bottom: 1px solid #1c2740; }
  #log { flex: 1; overflow-y: auto; padding: 14px; }
  .msg { max-width: 85%; margin: 8px 0; padding: 10px 14px; border-radius: 14px;
         line-height: 1.4; white-space: pre-wrap; word-wrap: break-word; }
  .me  { background: #1d4ed8; margin-left: auto; }
  .bot { background: #1c2740; margin-right: auto; }
  #status { text-align: center; font-size: 13px; color: #8aa0c4; padding: 6px; }
  #controls { display: flex; align-items: center; gap: 8px; padding: 10px 12px 18px; }
  #text { flex: 1; padding: 12px; border-radius: 10px; border: 1px solid #1c2740;
          background: #111a2e; color: #e6edf7; font-size: 16px; }
  button { border: 0; border-radius: 10px; padding: 12px 14px; font-size: 16px;
           background: #4cc9f0; color: #06101f; font-weight: 600; }
  #mic { width: 56px; height: 56px; border-radius: 50%; font-size: 24px; padding: 0; }
  #mic.on { background: #ef4444; color: white; animation: pulse 1s infinite; }
  @keyframes pulse { 50% { transform: scale(1.12); } }
  select { background: #111a2e; color: #e6edf7; border: 1px solid #1c2740;
           border-radius: 8px; padding: 6px; font-size: 14px; }
  #bar { text-align: center; padding: 6px; }
</style>
</head>
<body>
<header>JARVIS</header>
<div id="log"></div>
<div id="status">Waking up the server...</div>
<div id="bar">
  Language:
  <select id="lang">
    <option value="en-IN">English (India)</option>
    <option value="en-US">English (US)</option>
    <option value="hi-IN">Hindi</option>
  </select>
</div>
<div id="controls">
  <input id="text" type="text" placeholder="Or type here..." autocomplete="off">
  <button id="sendBtn">Send</button>
  <button id="mic">&#127908;</button>
</div>

<script>
  const log = document.getElementById('log');
  const statusEl = document.getElementById('status');
  const mic = document.getElementById('mic');
  const lang = document.getElementById('lang');
  const textBox = document.getElementById('text');
  const READY = 'Tap the mic and speak';

  function add(who, text) {
    const d = document.createElement('div');
    d.className = 'msg ' + who;
    d.textContent = text;
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
  }

  function speak(text) {
    if (!('speechSynthesis' in window)) return;
    speechSynthesis.cancel();
    const clean = text.replace(/[*#_`]/g, '');
    const u = new SpeechSynthesisUtterance(clean);
    u.lang = lang.value;
    u.rate = 1.05;
    speechSynthesis.speak(u);
  }

  // Wake the server up as soon as the page opens, so the first
  // message is not slow.
  fetch('/health')
    .then(() => { statusEl.textContent = READY; })
    .catch(() => { statusEl.textContent = READY; });

  async function send(text) {
    text = text.trim();
    if (!text) return;
    add('me', text);
    statusEl.textContent = 'JARVIS is thinking...';
    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 70000);
      const r = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
        signal: ctrl.signal
      });
      clearTimeout(timer);
      const data = await r.json();
      const reply = data.reply || data.error || 'No reply';
      add('bot', reply);
      if (data.reply) speak(reply);
    } catch (e) {
      add('bot', 'Could not reach the server. Please try again.');
    }
    statusEl.textContent = READY;
  }

  // Voice input
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let rec = null;
  if (SR) {
    rec = new SR();
    rec.interimResults = false;
    rec.onresult = (e) => { send(e.results[0][0].transcript); };
    rec.onend = () => { mic.classList.remove('on'); };
    rec.onerror = (e) => {
      mic.classList.remove('on');
      statusEl.textContent = 'Mic problem: ' + e.error + ' (allow microphone permission)';
    };
  }

  mic.onclick = () => {
    if (!rec) {
      statusEl.textContent = 'Voice input is not supported here. Try Chrome, or type.';
      return;
    }
    speechSynthesis.cancel();
    try {
      rec.lang = lang.value;
      rec.start();
      mic.classList.add('on');
      statusEl.textContent = 'Listening...';
    } catch (e) {}
  };

  document.getElementById('sendBtn').onclick = () => {
    send(textBox.value);
    textBox.value = '';
  };
  textBox.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { send(textBox.value); textBox.value = ''; }
  });

  add('bot', 'JARVIS online. Tap the mic and talk to me.');
</script>
</body>
</html>
"""


def safe_print(*args):
    """Print without ever crashing, even on strange characters."""
    try:
        print(*args, flush=True)
    except Exception:
        print("(could not print message)", flush=True)


def is_busy_error(error):
    """True if Google is overloaded, too slow, or the model is unavailable."""
    text = repr(error).lower()
    busy_words = [
        "503", "unavailable",          # Google is busy
        "504", "deadline",             # Google took too long
        "429", "resource_exhausted",   # sending too fast
        "timeout", "timed out",        # our own wait ran out
        "404", "not_found",            # model not available
    ]
    return any(word in text for word in busy_words)


def ask_gemini(model_name, message, fast_thinking):
    """Send one question to one model. fast_thinking=True asks for less thinking."""
    settings = {
        "system_instruction": SYSTEM_PROMPT,
        "max_output_tokens": 400,
    }
    if fast_thinking:
        settings["thinking_config"] = types.ThinkingConfig(thinking_level="low")

    return client.models.generate_content(
        model=model_name,
        contents=message,
        config=types.GenerateContentConfig(**settings),
    )


# If ANY error escapes, return it as JSON instead of an HTML page.
@app.errorhandler(Exception)
def handle_any_error(e):
    safe_print("UNHANDLED ERROR:", repr(e))
    safe_print(traceback.format_exc())
    return jsonify({"error": "Server error: " + repr(e)[:300]}), 500


@app.get("/")
def home():
    return "JARVIS Server is Online! Open /app on your phone."


@app.get("/app")
def phone_app():
    return Response(PAGE, mimetype="text/html")


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "JARVIS Server is healthy",
        "gemini_configured": client is not None,
        "models": MODELS
    })


@app.post("/chat")
def chat():
    if client is None:
        return jsonify({
            "error": "Server is missing GEMINI_API_KEY. Set it in Render's Environment tab and redeploy."
        }), 500

    data = request.get_json(silent=True) or {}
    user_message = str(data.get("message", "")).strip()

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    last_error = None

    for model_name in MODELS:
        try:
            try:
                response = ask_gemini(model_name, user_message, fast_thinking=True)
            except Exception as first_error:
                # If Google is busy, go to the next model.
                # If the "low thinking" setting was the problem, retry without it.
                if is_busy_error(first_error):
                    raise
                safe_print("Retrying without thinking setting:", repr(first_error)[:200])
                response = ask_gemini(model_name, user_message, fast_thinking=False)

            reply_text = response.text
            if not reply_text:
                reply_text = "(Gemini returned an empty reply)"

            safe_print("Answered by model:", model_name)
            return jsonify({"reply": str(reply_text), "model": model_name})

        except Exception as e:
            last_error = e
            safe_print("GEMINI ERROR with " + model_name + ":", repr(e))

            if is_busy_error(e):
                continue

            # Any other error (like a bad key) will not be fixed by another model.
            break

    if last_error is not None and is_busy_error(last_error):
        return jsonify({
            "error": "Google's AI is slow or busy right now. Please try again in a minute."
        }), 503

    return jsonify({"error": repr(last_error)[:500]}), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
