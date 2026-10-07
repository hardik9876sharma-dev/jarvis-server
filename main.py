import os
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)

# Read the API key from Render's Environment Variables.
raw_key = os.environ.get("GEMINI_API_KEY") or ""
GEMINI_API_KEY = raw_key.strip().strip('"').strip("'").strip()

# Models to try, in order. If the first one is busy, the server
# automatically tries the next one. You can edit this list later.
MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash-lite",
]

# How long to wait for Google on each try, in milliseconds (15 seconds).
GEMINI_TIMEOUT_MS = 15000

client = None
if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
    )
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
    """True if Google is overloaded, we are sending too fast, or it timed out."""
    text = repr(error).lower()
    return (
        "503" in text
        or "unavailable" in text
        or "429" in text
        or "timeout" in text
        or "timed out" in text
        or "404" in text      # model not available -> try the next one
        or "not_found" in text
    )


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
            response = client.models.generate_content(
                model=model_name,
                contents=user_message
            )

            reply_text = response.text
            if not reply_text:
                reply_text = "(Gemini returned an empty reply)"

            safe_print("Answered by model:", model_name)
            return jsonify({"reply": str(reply_text), "model": model_name})

        except Exception as e:
            last_error = e
            safe_print("GEMINI ERROR with " + model_name + ":", repr(e))

            # If Google is busy or the model is unavailable, try the next model.
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
