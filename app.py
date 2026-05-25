from flask import Flask, request, jsonify, render_template
from ai_model import build_client
import os

app = Flask(__name__)

client = build_client()
model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
chat = client.chats.create(model=model_name)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    user_text = request.json.get("message", "").strip()
    if not user_text:
        return jsonify({"error": "Empty message"}), 400
    try:
        response = chat.send_message(user_text)
        text = getattr(response, "text", None) or str(response)
        return jsonify({"reply": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
