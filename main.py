import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)

@app.get("/")
def home():
    return "JARVIS Server is Online!"

@app.get("/health")
def health():
    return jsonify({
        "status": "online",
        "assistant": "JARVIS"
    })

@app.post("/ask")
def ask():

    data = request.get_json()

    question = data.get("question", "").strip()

    if not question:
        return jsonify({
            "error": "No question received"
        }), 400

    response = client.responses.create(
        model="gpt-5.5",
        instructions="""
        You are JARVIS, a helpful AI assistant.

        Give clear and reasonably short answers
        because your answers will be spoken aloud.

        You are being used for a Class 12
        school project.
        """,
        input=question
    )

    return jsonify({
        "answer": response.output_text
    })


if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 8080)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )