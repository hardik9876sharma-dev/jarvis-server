import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai

app = Flask(__name__)
CORS(app)

# Read the API key from Render's Environment Variables.
# .get() returns None if the key is missing instead of crashing the app.
GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY is not set. /chat will return an error.")
    print(
        "Env vars that look related:",
        sorted(k for k in os.environ if "GEMINI" in k.upper() or "GOOGLE" in k.upper()),
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
        print("Error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
