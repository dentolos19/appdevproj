from flask import render_template, request

from main import app
from utils import require_login


@app.route("/chat")
@require_login
def chat():
    return render_template("chat.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    # Get the data from the request
    data: dict = request.get_json()
    prompt: str = data["prompt"]
    history: list[dict] = data["history"]

    # Get master prompt
    with open("src/static/masterprompt.txt", "r") as file:
        master_prompt = file.read()

    # Build history context
    ai_request = master_prompt + "\n"
    for message in history:
        role = message["role"]
        message = message["content"]
        ai_request += f"{role}: {message}\n"

    # Add the current prompt to the history
    ai_request += f"user (current prompt): {prompt}\n"

    # Generate a response
    ai_response = agent.generate_content(ai_request)
    ai_response_text = ai_response.candidates[0].content.parts[0].text.strip()

    return {"response": ai_response_text}