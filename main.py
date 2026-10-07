import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai

app = Flask(__name__)
CORS(app)

# Read the API key from Render's Environment Variables.
# .strip() removes spaces, and the second .strip() removes quotes
# in case the key was pasted with "quotes" around it.
raw_key = os.environ.get("GEMINI_API_KEY") or ""
GEMINI_API_KEY = raw_key.strip().strip('"').strip("'").strip()

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
    print("Gemini client created.", flush=True)
else:
    # flush=True makes the message show up in Render's logs right away
    print("WARNING: GEMINI_API_KEY is not set. /chat will return an error.", flush=True)
    print(
        "Env vars that look related:",
        sorted(k for k in os.environ if "GEMINI" in k.upper() or "GOOGLE" in k.upper()),
        flush=True,
    )


@app.get("/")
def home():
    return "JARVIS Server is Online!"


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "JARVIS Server is healthy",
        "gemini_configured": client is not None
    })


# TEMPORARY debug page. Shows variable NAMES and the key LENGTH only.
# Delete this whole function once everything works.
@app.get("/debug-env")
def debug_env():
    related = sorted(
        k for k in os.environ if "GEMINI" in k.upper() or "GOOGLE" in k.upper()
    )
    return jsonify({
        "related_variable_names": related,
        "GEMINI_API_KEY_exists": "GEMINI_API_KEY" in os.environ,
        "GEMINI_API_KEY_length": len(raw_key),
        "total_env_variables": len(os.environ)
    })


@app.post("/chat")
def chat():
    try:
        if client is None:
            return jsonify({
                "error": "Server is missing GEMINI_API_KEY. Set it in Render's Environment tab and redeploy."
            }), 500

        data = request.get_json(silent=True) or {}
        user_message = str(data.get("message", "")).strip()

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message
        )

        return jsonify({"reply": response.text})

    except Exception as e:
        print("Error:", e, flush=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
