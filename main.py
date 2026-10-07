import os
import traceback
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)

# ===============================================================
# GEMINI API KEY
# ===============================================================
# The API key is read from Render Environment Variables.
raw_key = os.environ.get("GEMINI_API_KEY") or ""
GEMINI_API_KEY = raw_key.strip().strip('"').strip("'").strip()

# ===============================================================
# GEMINI MODELS
# ===============================================================
# Models are tried in this order.
MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
]

# Gemini timeout in milliseconds.
GEMINI_TIMEOUT_MS = 12000

# ===============================================================
# JARVIS PERSONALITY
# ===============================================================
SYSTEM_PROMPT = (
    "You are JARVIS, a friendly AI voice assistant created and developed "
    "by Hardik Sharma as a Class 12 AI and IoT school project. "

    "If someone asks who created you, who made you, who developed you, "
    "who your creator is, or who is responsible for making you, answer: "
    "'I was created and developed by Hardik Sharma as his Class 12 AI and IoT project.' "

    "If someone asks what your project is, explain that you are an AI and IoT "
    "voice assistant project created by Hardik Sharma. "

    "If someone asks about your technology, explain that you use an ESP8266 "
    "for IoT hardware communication, a web interface for interaction, "
    "a cloud server for backend processing, and Gemini for AI responses. "

    "Do not claim that Hardik Sharma trained the Gemini AI model itself. "
    "He created and developed the JARVIS project and its integration. "

    "Be polite, confident, helpful, and friendly. "
    "Reply in 1 to 3 short sentences. "
    "Use plain words only: no markdown, no lists, no emojis, no asterisks. "
    "Reply in the same language the user speaks."
)

# ===============================================================
# GEMINI CLIENT
# ===============================================================
client = None

if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
    )
    print("Gemini client created.", flush=True)
else:
    print(
        "WARNING: GEMINI_API_KEY is not set. /chat will return an error.",
        flush=True,
    )


# ===============================================================
# PHONE WEBSITE
# ===============================================================
PAGE = """<!DOCTYPE html>
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

/* =========================================================
   HEADER
   ========================================================= */

header {
    padding: 14px 16px 10px;
    text-align: center;

    font-size: 22px;
    font-weight: 700;

    letter-spacing: 6px;
    color: #4cc9f0;

    border-bottom: 1px solid #1c2740;

    text-shadow:
        0 0 8px rgba(76, 201, 240, 0.7),
        0 0 20px rgba(76, 201, 240, 0.3);
}

.creator {
    text-align: center;
    font-size: 11px;
    letter-spacing: 2px;
    color: #7185a8;
    padding-top: 5px;
}

/* =========================================================
   STATUS
   ========================================================= */

#systemStatus {
    display: flex;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;

    padding: 8px 10px;

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

/* =========================================================
   JARVIS CORE
   ========================================================= */

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

/* =========================================================
   CHAT
   ========================================================= */

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

    box-shadow:
        0 3px 10px rgba(29, 78, 216, 0.25);
}

.bot {
    background: #1c2740;
    margin-right: auto;

    border: 1px solid #263654;

    box-shadow:
        0 3px 10px rgba(0, 0, 0, 0.25);
}

/* =========================================================
   STATUS TEXT
   ========================================================= */

#status {
    text-align: center;

    font-size: 13px;

    color: #8aa0c4;

    padding: 6px;
}

/* =========================================================
   LANGUAGE
   ========================================================= */

#bar {
    text-align: center;

    padding: 6px;
}

select {
    background: #111a2e;

    color: #e6edf7;

    border: 1px solid #1c2740;

    border-radius: 8px;

    padding: 6px;

    font-size: 14px;
}

/* =========================================================
   CONTROLS
   ========================================================= */

#controls {
    display: flex;

    align-items: center;

    gap: 8px;

    padding: 10px 12px 18px;
}

#text {
    flex: 1;

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

    box-shadow:
        0 0 8px rgba(76, 201, 240, 0.2);
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

</style>
</head>


<body>

<header>
    JARVIS
</header>

<div class="creator">
    CREATED & DEVELOPED BY HARDIK SHARMA
</div>


<!-- SYSTEM STATUS -->

<div id="systemStatus">

    <div class="statusItem">
        AI: <span class="online">ONLINE</span>
    </div>

    <div class="statusItem">
        SERVER: <span class="online">ONLINE</span>
    </div>

    <div class="statusItem">
        ESP8266: <span class="online">READY</span>
    </div>

</div>


<!-- JARVIS CORE -->

<div id="coreArea">

    <div id="core">
        JARVIS
    </div>

</div>


<!-- CHAT -->

<div id="log"></div>


<div id="status">
    Waking up the server...
</div>


<!-- LANGUAGE -->

<div id="bar">

    Language:

    <select id="lang">

        <option value="en-IN">
            English (India)
        </option>

        <option value="en-US">
            English (US)
        </option>

        <option value="hi-IN">
            Hindi
        </option>

    </select>

</div>


<!-- CONTROLS -->

<div id="controls">

    <input
        id="text"
        type="text"
        placeholder="Ask JARVIS..."
        autocomplete="off"
    >

    <button id="sendBtn">
        Send
    </button>

    <button id="mic">
        &#127908;
    </button>

</div>


<script>

const log = document.getElementById('log');

const statusEl =
    document.getElementById('status');

const mic =
    document.getElementById('mic');

const lang =
    document.getElementById('lang');

const textBox =
    document.getElementById('text');

const core =
    document.getElementById('core');


const READY =
    'Tap the mic and speak';


/* =========================================================
   ADD MESSAGE
   ========================================================= */

function add(who, text) {

    const d =
        document.createElement('div');

    d.className =
        'msg ' + who;

    d.textContent =
        text;

    log.appendChild(d);

    log.scrollTop =
        log.scrollHeight;
}


/* =========================================================
   VOICE OUTPUT
   ========================================================= */

function speak(text) {

    if (!('speechSynthesis' in window)) {
        return;
    }

    speechSynthesis.cancel();

    const clean =
        text.replace(/[*#_`]/g, '');

    const u =
        new SpeechSynthesisUtterance(clean);

    u.lang =
        lang.value;

    u.rate =
        1.05;

    speechSynthesis.speak(u);
}


/* =========================================================
   CORE STATUS
   ========================================================= */

function setCore(state) {

    core.classList.remove(
        'listening',
        'thinking'
    );

    if (state === 'listening') {

        core.classList.add('listening');

        core.textContent =
            'LISTENING';

    }
    else if (state === 'thinking') {

        core.classList.add('thinking');

        core.textContent =
            'THINKING';

    }
    else {

        core.textContent =
            'JARVIS';

    }
}


/* =========================================================
   HEALTH CHECK
   ========================================================= */

fetch('/health')

    .then(() => {

        statusEl.textContent =
            READY;

    })

    .catch(() => {

        statusEl.textContent =
            READY;

    });


/* =========================================================
   SEND MESSAGE
   ========================================================= */

async function send(text) {

    text =
        text.trim();

    if (!text) {
        return;
    }


    add(
        'me',
        text
    );


    statusEl.textContent =
        'JARVIS is thinking...';


    setCore('thinking');


    try {

        const ctrl =
            new AbortController();


        const timer =
            setTimeout(
                () => ctrl.abort(),
                70000
            );


        const r =
            await fetch(
                '/chat',
                {
                    method: 'POST',

                    headers: {
                        'Content-Type':
                            'application/json'
                    },

                    body:
                        JSON.stringify({
                            message: text
                        }),

                    signal:
                        ctrl.signal
                }
            );


        clearTimeout(timer);


        const data =
            await r.json();


        const reply =
            data.reply ||
            data.error ||
            'No reply';


        add(
            'bot',
            reply
        );


        if (data.reply) {

            speak(
                reply
            );

        }

    }

    catch (e) {

        add(
            'bot',
            'Could not reach the server. Please try again.'
        );

    }


    setCore('ready');


    statusEl.textContent =
        READY;
}


/* =========================================================
   VOICE INPUT
   ========================================================= */

const SR =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;


let rec =
    null;


if (SR) {

    rec =
        new SR();


    rec.interimResults =
        false;


    rec.onresult =
        (e) => {

            send(
                e.results[0][0].transcript
            );

        };


    rec.onend =
        () => {

            mic.classList.remove(
                'on'
            );

            setCore('ready');

        };


    rec.onerror =
        (e) => {

            mic.classList.remove(
                'on'
            );

            setCore('ready');

            statusEl.textContent =
                'Mic problem: ' +
                e.error +
                ' (allow microphone permission)';

        };
}


/* =========================================================
   MICROPHONE BUTTON
   ========================================================= */

mic.onclick =
    () => {

        if (!rec) {

            statusEl.textContent =
                'Voice input is not supported here. Try Chrome, or type.';

            return;
        }


        speechSynthesis.cancel();


        try {

            rec.lang =
                lang.value;


            rec.start();


            mic.classList.add(
                'on'
            );


            setCore(
                'listening'
            );


            statusEl.textContent =
                'Listening...';

        }

        catch (e) {

            // Prevent errors if the microphone
            // is already running.

        }

    };


/* =========================================================
   SEND BUTTON
   ========================================================= */

document
    .getElementById('sendBtn')
    .onclick =
    () => {

        send(
            textBox.value
        );

        textBox.value =
            '';

    };


/* =========================================================
   ENTER KEY
   ========================================================= */

textBox.addEventListener(
    'keydown',
    (e) => {

        if (e.key === 'Enter') {

            send(
                textBox.value
            );

            textBox.value =
                '';

        }

    }
);


/* =========================================================
   STARTUP MESSAGE
   ========================================================= */

add(
    'bot',
    'JARVIS online. Created and developed by Hardik Sharma. Tap the mic and talk to me.'
);

</script>

</body>
</html>
"""


# ===============================================================
# SAFE PRINT
# ===============================================================

def safe_print(*args):
    """Print without crashing on strange characters."""

    try:
        print(*args, flush=True)

    except Exception:
        print(
            "(could not print message)",
            flush=True
        )


# ===============================================================
# ERROR DETECTION
# ===============================================================

def is_busy_error(error):
    """Return True if Google is overloaded, slow, or unavailable."""

    text = repr(error).lower()

    busy_words = [
        "503",
        "unavailable",

        "504",
        "deadline",

        "429",
        "resource_exhausted",

        "timeout",
        "timed out",

        "404",
        "not_found",
    ]

    return any(
        word in text
        for word in busy_words
    )


# ===============================================================
# ASK GEMINI
# ===============================================================

def ask_gemini(
    model_name,
    message,
    fast_thinking
):

    settings = {

        "system_instruction":
            SYSTEM_PROMPT,

        "max_output_tokens":
            400,
    }


    if fast_thinking:

        settings[
            "thinking_config"
        ] = types.ThinkingConfig(
            thinking_level="low"
        )


    return client.models.generate_content(

        model=model_name,

        contents=message,

        config=
            types.GenerateContentConfig(
                **settings
            ),
    )


# ===============================================================
# GLOBAL ERROR HANDLER
# ===============================================================

@app.errorhandler(Exception)
def handle_any_error(e):

    safe_print(
        "UNHANDLED ERROR:",
        repr(e)
    )

    safe_print(
        traceback.format_exc()
    )

    return jsonify({

        "error":
            "Server error: " +
            repr(e)[:300]

    }), 500


# ===============================================================
# HOME
# ===============================================================

@app.get("/")
def home():

    return (
        "JARVIS Server is Online! "
        "Open /app on your phone."
    )


# ===============================================================
# PHONE APP
# ===============================================================

@app.get("/app")
def phone_app():

    return Response(
        PAGE,
        mimetype="text/html"
    )


# ===============================================================
# HEALTH
# ===============================================================

@app.get("/health")
def health():

    return jsonify({

        "status":
            "ok",

        "message":
            "JARVIS Server is healthy",

        "gemini_configured":
            client is not None,

        "models":
            MODELS
    })


# ===============================================================
# CHAT
# ===============================================================

@app.post("/chat")
def chat():

    if client is None:

        return jsonify({

            "error":
                "Server is missing GEMINI_API_KEY. "
                "Set it in Render's Environment tab and redeploy."

        }), 500


    data =
        request.get_json(
            silent=True
        ) or {}


    user_message =
        str(
            data.get(
                "message",
                ""
            )
        ).strip()


    if not user_message:

        return jsonify({

            "error":
                "Message is required"

        }), 400


    last_error =
        None


    # Try each Gemini model.
    for model_name in MODELS:

        try:

            try:

                response =
                    ask_gemini(
                        model_name,
                        user_message,
                        fast_thinking=True
                    )

            except Exception as first_error:

                # If Google is busy, try the next model.
                if is_busy_error(
                    first_error
                ):

                    raise


                safe_print(
                    "Retrying without thinking setting:",
                    repr(first_error)[:200]
                )


                response =
                    ask_gemini(
                        model_name,
                        user_message,
                        fast_thinking=False
                    )


            reply_text =
                response.text


            if not reply_text:

                reply_text =
                    "(Gemini returned an empty reply)"


            safe_print(
                "Answered by model:",
                model_name
            )


            return jsonify({

                "reply":
                    str(reply_text),

                "model":
                    model_name

            })


        except Exception as e:

            last_error =
                e


            safe_print(
                "GEMINI ERROR with " +
                model_name +
                ":",
                repr(e)
            )


            # If it is a temporary/busy error,
            # try the next model.
            if is_busy_error(e):

                continue


            # Other errors, such as a bad API key,
            # won't normally be fixed by another model.
            break


    # ===========================================================
    # ALL MODELS FAILED
    # ===========================================================

    if (
        last_error is not None
        and
        is_busy_error(last_error)
    ):

        return jsonify({

            "error":
                "Google's AI is slow or busy right now. "
                "Please try again in a minute."

        }), 503


    return jsonify({

        "error":
            repr(last_error)[:500]

    }), 500


# ===============================================================
# LOCAL SERVER
# ===============================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
    )
