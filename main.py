import os

from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Hugging Face token
HF_TOKEN = os.environ.get("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN is missing from Render Environment Variables")

# Hugging Face OpenAI-compatible API
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)


@app.get("/")
def home():
    return "JARVIS Server is Online!"


@app.get("/health")
def health():
    return jsonify({
        "status": "ok"
    })


@app.post("/ask")
def ask():
    data = request.get_json(silent=True) or {}

    question = data.get("question", "").strip()

    if not question:
        return jsonify({
            "error": "No question provided"
        }), 400

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b:fastest",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are JARVIS, a helpful voice assistant. "
                        "Give short, clear and useful answers."
                    )
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            max_tokens=150
        )

        answer = response.choices[0].message.content

        return jsonify({
            "answer": answer
        })

    except Exception as e:
        print("AI ERROR:", repr(e))

        return jsonify({
            "error": "AI request failed",
            "details": str(e)
        }), 500