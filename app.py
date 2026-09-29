import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import MODEL_NAME, REFUSAL_MESSAGE, SYSTEM_PROMPT

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MAX_HISTORY = 10  # number of recent messages sent back to the model


def build_contents(history, message):
    """Convert chat history and the new message into Gemini's format."""
    contents = []
    for item in history[-MAX_HISTORY:]:
        role = "user" if item.get("role") == "user" else "model"
        contents.append(
            types.Content(role=role, parts=[types.Part(text=item.get("text", ""))])
        )
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))
    return contents


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not message:
        return jsonify({"reply": "Please type a question first."}), 400

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=build_contents(history, message),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.6,
            ),
        )
        reply = (response.text or "").strip() or REFUSAL_MESSAGE
        return jsonify({"reply": reply})
    except Exception as error:
        print(f"Gemini error: {error}")
        return jsonify({"reply": "Something went wrong. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=True)
