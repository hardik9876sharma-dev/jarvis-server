import os
import time
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai

app = Flask(__name__)
CORS(app)

# Read the API key from Render's Environment Variables.
raw_key = os.environ.get("GEMINI_API_KEY") or ""
GEMINI_API_KEY = raw_key.strip().strip('"').strip("'").strip()

# The AI model to use. If Google retires it in the future,
# change only this one line.
MODEL_NAME = "gemini-3.8-flash"

# How many times to try when Google says "busy" (503) or "slow down" (429).
MAX_TRIES = 3

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
    print("Gemini client created.", flush=True)
else:
    print("WARNING: GEMINI_API_KEY is not set. /chat will return an error.", flush=True)


def safe_print(*args):
    """Print without ever crashing, even on strange characters."""
    try:
        print(*args, flush=True)
    except Exception:
        print("(could not print message)", flush=True)


def is_busy_error(error):
    """True if Google says it is overloaded or we are sending too fast."""
    text = repr(error)
    return "503" in text or "UNAVAILABLE" in text or "429" in text


# If ANY error escapes, return it as JSON instead of an HTML page.
@app.errorhandler(Exception)
def handle_any_error(e):
    safe_print("UNHANDLED ERROR:", repr(e))
    safe_print(traceback.format_exc())
    return jsonify({"error": "Server error: " + repr(e)[:300]}), 500


@app.get("/")
def home():
    return "JARVIS Server is Online!"


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "JARVIS Server is healthy",
        "gemini_configured": client is not None,
        "model": MODEL_NAME
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

    for attempt in range(1, MAX_TRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=user_message
            )

            reply_text = response.text
            if not reply_text:
                reply_text = "(Gemini returned an empty reply)"

            return jsonify({"reply": str(reply_text)})

        except Exception as e:
            last_error = e
            safe_print("GEMINI ERROR (try " + str(attempt) + "):", repr(e))

            # Only retry if Google is busy. Other errors will not fix themselves.
            if is_busy_error(e) and attempt < MAX_TRIES:
                time.sleep(attempt)  # wait 1 second, then 2 seconds
                continue

            break

    if last_error is not None and is_busy_error(last_error):
        return jsonify({
            "error": "Google's AI is very busy right now. Please try again in a minute."
        }), 503

    return jsonify({"error": repr(last_error)[:500]}), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
