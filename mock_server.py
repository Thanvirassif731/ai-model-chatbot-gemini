import os
from flask import Flask, request, jsonify, send_from_directory
from ai_model import build_client, CONVERSATION_STYLES

app = Flask(__name__, static_folder='.', static_url_path='')

# Initialize Gemini Client
init_error = None
client = None
chat = None

def init_chat_session(style_id="4"):
    global chat, init_error, client
    try:
        if client is None:
            client = build_client()
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        chat = client.chats.create(model=model_name)
        
        style = CONVERSATION_STYLES.get(style_id, CONVERSATION_STYLES["4"])
        system_prompt = style["prompt"]
        chat.send_message(f"[System Instructions: {system_prompt}]\n\nReady to chat! Keep these instructions in mind for all future responses.")
        init_error = None
        return True
    except Exception as e:
        print(f"Error initializing Gemini: {e}")
        init_error = str(e)
        chat = None
        return False

# Initial default setup
init_chat_session("4")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    # This serves style.css and script.js
    return send_from_directory('.', path)

@app.route('/styles', methods=['GET'])
def get_styles():
    return jsonify(CONVERSATION_STYLES)

@app.route('/init', methods=['POST'])
def init_endpoint():
    data = request.json or {}
    style_id = data.get('style_id', '4')
    success = init_chat_session(style_id)
    if success:
        return jsonify({"status": "initialized", "style": CONVERSATION_STYLES.get(style_id, {}).get("name")})
    else:
        return jsonify({"error": f"Failed to initialize chat: {init_error}"}), 500

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    if not chat:
        return jsonify({"error": f"Chat client not initialized. Error: {init_error}"}), 500
        
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "No message provided"}), 400
        
    user_message = data['message']
    
    try:
        response = chat.send_message(user_message)
        # Handle the response structure from google-genai
        text = getattr(response, "text", None) or str(response)
        return jsonify({"response": text})
    except Exception as e:
        print(f"Error generating response: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server for UI at http://127.0.0.1:5000")
    app.run(port=5000, debug=True)
