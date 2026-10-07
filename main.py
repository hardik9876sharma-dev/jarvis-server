import os
import traceback

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from google import genai
from google.genai import types

# ============================================================
# JARVIS SETTINGS
# ============================================================

APP_NAME = "JARVIS"
CREATOR_NAME = "Hardik Sharma"

# Gemini models are kept in fallback order.
MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
]

SYSTEM_PROMPT = f"""
You are {APP_NAME}, a friendly AI voice assistant created and developed by
{CREATOR_NAME} as a Class 12 AI and IoT school project.

If someone asks who created you, who made you, who developed you, or who your
creator is, answer exactly:
"I was created and developed by Hardik Sharma as his Class 12 AI and IoT project."

If someone asks what your project is, explain that you are an AI and IoT voice
assistant project created by Hardik Sharma.

If someone asks about your technology, explain that the project uses an ESP8266
for IoT hardware communication, a web interface for phone interaction, a cloud
server for backend processing, and Gemini for AI responses.

Do not claim that Hardik Sharma trained the Gemini AI model itself. He created
and developed this JARVIS project and its integration.

Be polite, confident, helpful, and friendly.
Keep normal answers short, usually 1 to 3 sentences.
Use plain text without markdown, bullet points, emojis, or asterisks.
Reply in the same language as the user when reasonably possible.
"""

# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)
CORS(app)

# ============================================================
# GEMINI CLIENT
# ============================================================

GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()

client = None

if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print("Gemini client created.", flush=True)
    except Exception as e:
        print("Gemini client creation failed:", repr(e), flush=True)
        client = None
else:
    print("WARNING: GEMINI_API_KEY is not set.", flush=True)

# ============================================================
# PHONE WEB APP
# ============================================================

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#050b16">
<title>JARVIS - Hardik Sharma</title>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background:
        radial-gradient(circle at center, #10213d 0%, #050b16 45%, #02050a 100%);
    color: #e6edf7;
    font-family: system-ui, Arial, sans-serif;
    display: flex;
    flex-direction: column;
    height: 100vh;
    height: 100dvh;
    overflow: hidden;
}

header {
    padding: 14px 16px 8px;
    text-align: center;
    font-size: 23px;
    font-weight: 700;
    letter-spacing: 6px;
    color: #4cc9f0;
    text-shadow:
        0 0 8px rgba(76, 201, 240, 0.7),
        0 0 20px rgba(76, 201, 240, 0.3);
}

.creator {
    text-align: center;
    font-size: 11px;
    letter-spacing: 2px;
    color: #7185a8;
    padding-bottom: 7px;
}

#systemStatus {
    display: flex;
    justify-content: center;
    gap: 8px;
    flex-wrap: wrap;
    padding: 7px 10px;
    font-size: 11px;
    color: #8aa0c4;
}

.statusItem {
    padding: 5px 8px;
    border: 1px solid #1c2740;
    border-radius: 20px;
    background: rgba(17, 26, 46, 0.8);
}

.online {
    color: #4ade80;
}

#coreArea {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 10px 0 4px;
}

#core {
    width: 105px;
    height: 105px;
    border-radius: 50%;
    border: 2px solid #4cc9f0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #4cc9f0;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 2px;
    background:
        radial-gradient(circle,
        rgba(76, 201, 240, 0.25),
        rgba(76, 201, 240, 0.03) 60%,
        transparent 70%);
    box-shadow:
        0 0 12px rgba(76, 201, 240, 0.8),
        0 0 35px rgba(76, 201, 240, 0.3);
    transition: 0.3s;
}

#core.listening {
    border-color: #ef4444;
    color: #ef4444;
    box-shadow:
        0 0 15px rgba(239, 68, 68, 0.9),
        0 0 45px rgba(239, 68, 68, 0.4);
    animation: pulse 1s infinite;
}

#core.thinking {
    border-color: #facc15;
    color: #facc15;
    box-shadow:
        0 0 15px rgba(250, 204, 21, 0.9),
        0 0 45px rgba(250, 204, 21, 0.4);
    animation: pulse 0.8s infinite;
}

@keyframes pulse {
    50% {
        transform: scale(1.08);
    }
}

#log {
    flex: 1;
    overflow-y: auto;
    padding: 10px 14px 14px;
}

.msg {
    max-width: 85%;
    margin: 8px 0;
    padding: 10px 14px;
    border-radius: 14px;
    line-height: 1.4;
    white-space: pre-wrap;
    word-wrap: break-word;
}

.me {
    background: #1d4ed8;
    margin-left: auto;
}

.bot {
    background: #1c2740;
    margin-right: auto;
    border: 1px solid #263654;
}

#status {
    text-align: center;
    font-size: 13px;
    color: #8aa0c4;
    padding: 6px;
}

#bar {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    padding: 6px 10px;
}

select {
    background: #111a2e;
    color: #e6edf7;
    border: 1px solid #1c2740;
    border-radius: 8px;
    padding: 6px;
    font-size: 14px;
}

#controls {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px 18px;
}

#text {
    flex: 1;
    min-width: 0;
    padding: 12px;
    border-radius: 10px;
    border: 1px solid #1c2740;
    background: #111a2e;
    color: #e6edf7;
    font-size: 16px;
    outline: none;
}

#text:focus {
    border-color: #4cc9f0;
}

button {
    border: 0;
    border-radius: 10px;
    padding: 12px 14px;
    font-size: 16px;
    background: #4cc9f0;
    color: #06101f;
    font-weight: 600;
    cursor: pointer;
}

button:active {
    transform: scale(0.96);
}

#mic {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    font-size: 24px;
    padding: 0;
}

#mic.on {
    background: #ef4444;
    color: white;
    animation: pulse 1s infinite;
}

#voiceSettings {
    font-size: 12px;
}

@media (max-width: 500px) {
    #core {
        width: 90px;
        height: 90px;
    }

    header {
        font-size: 20px;
    }

    #controls button#sendBtn {
        padding-left: 11px;
        padding-right: 11px;
    }
}
</style>
</head>

<body>

<header>JARVIS</header>

<div class="creator">CREATED &amp; DEVELOPED BY HARDIK SHARMA</div>

<div id="systemStatus">
    <div class="statusItem">AI: <span class="online">ONLINE</span></div>
    <div class="statusItem">SERVER: <span class="online">ONLINE</span></div>
    <div class="statusItem">ESP8266: <span class="online">READY</span></div>
</div>

<div id="coreArea">
    <div id="core">JARVIS</div>
</div>

<div id="log"></div>

<div id="status">Starting JARVIS...</div>

<div id="bar">
    <label for="lang">Language:</label>

    <select id="lang">
        <option value="en-IN">English (India)</option>
        <option value="en-US">English (US)</option>
        <option value="hi-IN">Hindi</option>
    </select>

    <label for="voiceSelect">Voice:</label>

    <select id="voiceSelect">
        <option value="">Default voice</option>
    </select>
</div>

<div id="bar">
    <label for="rate">Speed:</label>
    <input id="rate" type="range" min="0.70" max="1.20" step="0.05" value="0.90">

    <label for="pitch">Pitch:</label>
    <input id="pitch" type="range" min="0.50" max="1.30" step="0.05" value="0.75">
</div>

<div id="controls">
    <input
        id="text"
        type="text"
        placeholder="Ask JARVIS..."
        autocomplete="off"
    >

    <button id="sendBtn">Send</button>

    <button id="mic" title="Speak">&#127908;</button>
</div>

<script>
const APP_NAME = "JARVIS";

const log = document.getElementById("log");
const statusEl = document.getElementById("status");
const mic = document.getElementById("mic");
const lang = document.getElementById("lang");
const textBox = document.getElementById("text");
const core = document.getElementById("core");
const voiceSelect = document.getElementById("voiceSelect");
const rateSlider = document.getElementById("rate");
const pitchSlider = document.getElementById("pitch");

const READY = "Tap the mic and speak";

let voices = [];
let rec = null;

function add(who, text) {
    const d = document.createElement("div");
    d.className = "msg " + who;
    d.textContent = text;
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
}

function loadVoices() {
    if (!("speechSynthesis" in window)) {
        return;
    }

    voices = speechSynthesis.getVoices();

    voiceSelect.innerHTML = "";

    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = "Default voice";
    voiceSelect.appendChild(defaultOption);

    voices.forEach((voice, index) => {
        const option = document.createElement("option");
        option.value = String(index);
        option.textContent = voice.name + " (" + voice.lang + ")";
        voiceSelect.appendChild(option);
    });
}

if ("speechSynthesis" in window) {
    loadVoices();
    speechSynthesis.onvoiceschanged = loadVoices;
}

function speak(text) {
    if (!("speechSynthesis" in window)) {
        return;
    }

    speechSynthesis.cancel();

    const clean = String(text)
        .replace(/[*#_`]/g, "")
        .replace(/\s+/g, " ")
        .trim();

    if (!clean) {
        return;
    }

    const utterance = new SpeechSynthesisUtterance(clean);

    utterance.lang = lang.value;

    const selectedIndex = voiceSelect.value;

    if (selectedIndex !== "" && voices[Number(selectedIndex)]) {
        utterance.voice = voices[Number(selectedIndex)];
    } else {
        const preferred = voices.find(v =>
            v.lang.toLowerCase() === lang.value.toLowerCase()
        );

        if (preferred) {
            utterance.voice = preferred;
        }
    }

    // Jarvis-style starting settings.
    utterance.rate = Number(rateSlider.value);
    utterance.pitch = Number(pitchSlider.value);
    utterance.volume = 1.0;

    speechSynthesis.speak(utterance);
}

function setCore(state) {
    core.classList.remove("listening", "thinking");

    if (state === "listening") {
        core.classList.add("listening");
        core.textContent = "LISTENING";
    } else if (state === "thinking") {
        core.classList.add("thinking");
        core.textContent = "THINKING";
    } else {
        core.textContent = APP_NAME;
    }
}

async function checkHealth() {
    try {
        const response = await fetch("/health");
        const data = await response.json();

        if (data.gemini_configured) {
            statusEl.textContent = READY;
        } else {
            statusEl.textContent = "Gemini API key is not configured";
        }
    } catch (e) {
        statusEl.textContent = "Server connection problem";
    }
}

async function send(message) {
    message = String(message || "").trim();

    if (!message) {
        return;
    }

    add("me", message);

    statusEl.textContent = APP_NAME + " is thinking...";
    setCore("thinking");

    try {
        const controller = new AbortController();

        const timer = setTimeout(() => {
            controller.abort();
        }, 70000);

        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            }),
            signal: controller.signal
        });

        clearTimeout(timer);

        let data;

        try {
            data = await response.json();
        } catch (jsonError) {
            throw new Error("The server returned an invalid response.");
        }

        const reply =
            data.reply ||
            data.error ||
            "No reply received.";

        add("bot", reply);

        if (data.reply) {
            speak(data.reply);
        }

        if (!response.ok) {
            statusEl.textContent = "Server returned an error";
        }

    } catch (e) {
        add(
            "bot",
            "I could not reach the server. Please try again."
        );

        statusEl.textContent =
            e.name === "AbortError"
                ? "Request timed out"
                : "Connection problem";
    }

    setCore("ready");

    if (statusEl.textContent !== "Server returned an error" &&
        statusEl.textContent !== "Request timed out" &&
        statusEl.textContent !== "Connection problem") {
        statusEl.textContent = READY;
    }
}

const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;

if (SpeechRecognition) {
    rec = new SpeechRecognition();

    rec.interimResults = false;
    rec.continuous = false;

    rec.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        send(transcript);
    };

    rec.onend = function() {
        mic.classList.remove("on");
        setCore("ready");
    };

    rec.onerror = function(event) {
        mic.classList.remove("on");
        setCore("ready");

        statusEl.textContent =
            "Mic problem: " +
            event.error +
            " (allow microphone permission)";
    };
}

mic.onclick = function() {
    if (!rec) {
        statusEl.textContent =
            "Voice input is not supported here. Try Chrome or type your message.";
        return;
    }

    speechSynthesis.cancel();

    try {
        rec.lang = lang.value;
        rec.start();

        mic.classList.add("on");
        setCore("listening");
        statusEl.textContent = "Listening...";
    } catch (e) {
        // Prevent errors if recognition is already running.
    }
};

document.getElementById("sendBtn").onclick = function() {
    send(textBox.value);
    textBox.value = "";
    textBox.focus();
};

textBox.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        send(textBox.value);
        textBox.value = "";
    }
});

lang.addEventListener("change", function() {
    loadVoices();
});

add(
    "bot",
    "JARVIS online. Created and developed by Hardik Sharma. Tap the mic and talk to me."
);

checkHealth();
</script>

</body>
</html>
"""

# ============================================================
# HELPERS
# ============================================================

def is_temporary_error(error):
    text = repr(error).lower()

    temporary_words = [
        "429",
        "500",
        "502",
        "503",
        "504",
        "timeout",
        "timed out",
        "deadline",
        "unavailable",
        "resource_exhausted",
        "overloaded",
        "service unavailable",
    ]

    return any(word in text for word in temporary_words)


def ask_gemini(model_name, message):
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        max_output_tokens=400,
        thinking_config=types.ThinkingConfig(
            thinking_level="low"
        ),
    )

    return client.models.generate_content(
        model=model_name,
        contents=message,
        config=config,
    )


# ============================================================
# ERROR HANDLER
# ============================================================

@app.errorhandler(Exception)
def handle_any_error(error):
    print("UNHANDLED ERROR:", repr(error), flush=True)
    print(traceback.format_exc(), flush=True)

    return jsonify({
        "error": "Server error: " + repr(error)[:300]
    }), 500


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return "JARVIS Server is Online! Open /app on your phone."


# ============================================================
# PHONE APP
# ============================================================

@app.get("/app")
def phone_app():
    return Response(PAGE, mimetype="text/html")


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "JARVIS Server is healthy",
        "gemini_configured": client is not None,
        "models": MODELS
    })


# ============================================================
# CHAT
# ============================================================

@app.post("/chat")
def chat():
    if client is None:
        return jsonify({
            "error": (
                "Server is missing GEMINI_API_KEY. "
                "Set GEMINI_API_KEY in Render Environment Variables "
                "and redeploy."
            )
        }), 500

    data = request.get_json(silent=True) or {}

    user_message = str(data.get("message", "")).strip()

    if not user_message:
        return jsonify({
            "error": "Message is required"
        }), 400

    last_error = None

    for model_name in MODELS:
        try:
            response = ask_gemini(model_name, user_message)

            reply_text = getattr(response, "text", None)

            if not reply_text:
                reply_text = "I received the request, but Gemini returned an empty reply."

            reply_text = str(reply_text).strip()

            print(
                "Answered by model:",
                model_name,
                flush=True
            )

            return jsonify({
                "reply": reply_text,
                "model": model_name
            })

        except Exception as error:
            last_error = error

            print(
                "GEMINI ERROR with " + model_name + ":",
                repr(error),
                flush=True
            )

            if is_temporary_error(error):
                continue

            break

    if last_error is not None and is_temporary_error(last_error):
        return jsonify({
            "error": (
                "Google's AI service is busy or temporarily unavailable. "
                "Please try again in a minute."
            )
        }), 503

    return jsonify({
        "error": "Gemini request failed: " + repr(last_error)[:500]
    }), 500


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))

    app.run(
        host="0.0.0.0",
        port=port
    )
