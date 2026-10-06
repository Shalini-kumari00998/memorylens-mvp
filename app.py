"""
Part 5: AI-Native MVP — Conversational Photo Retrieval Assistant
A web app that helps users retrieve vaguely-remembered photos
by translating episodic memory descriptions into structured search queries.
"""

from __future__ import annotations

import os
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")

# Lazy-import Gemini so the app starts fine even without the package
_model = None

def _get_model():
    global _model
    if _model is None and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
        try:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=GEMINI_API_KEY)
            _model = genai.GenerativeModel("gemini-2.0-flash")
        except Exception as e:
            print(f"[Gemini init error] {e}")
    return _model

# In-memory conversation store (keyed by session; simple demo version)
conversations: dict = {}


SYSTEM_PROMPT = """You are MemoryLens — an AI assistant built into Google Photos that helps users find photos they vaguely remember.

Your job is to:
1. Ask warm, natural follow-up questions to extract partial memory clues
2. Build a structured search query from those clues
3. Present the user a clear "search plan" they can verify before running

You understand that users remember photos through:
- Emotional context (was I happy/sick/excited?)
- Occasion type (birthday, trip, hospital, school event)
- Visual scene details (colors, objects, people, lighting)
- Rough temporal anchor (last year, summer, 2022)
- Location or setting (beach, indoor, Goa, my friend's house)

Conversation rules:
- Ask only ONE question at a time to not overwhelm
- After 3-4 exchanges, synthesize into a structured query
- Format the final query as JSON inside <search_query> tags
- Be warm, helpful, and brief

When you have enough clues, output:
<search_query>
{
  "occasion": "...",
  "approximate_year": "...",
  "location_context": "...",
  "scene_details": ["...", "..."],
  "people_or_subjects": "...",
  "search_summary": "One line description of what to look for"
}
</search_query>
"""


def chat_with_gemini(session_id: str, user_message: str) -> str:
    """Maintains conversation history and calls Gemini."""
    if session_id not in conversations:
        conversations[session_id] = []

    conversations[session_id].append({
        "role": "user",
        "parts": [user_message],
    })

    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        return _demo_response(len(conversations[session_id]))

    model = _get_model()
    if model is None:
        return _demo_response(len(conversations[session_id]))

    try:
        chat = model.start_chat(history=conversations[session_id][:-1])
        full_prompt = SYSTEM_PROMPT + "\n\nUser: " + user_message
        response = chat.send_message(full_prompt)
        reply = response.text

        conversations[session_id].append({
            "role": "model",
            "parts": [reply],
        })
        return reply
    except Exception as e:
        return f"[Error calling Gemini: {e}] Please check your API key."


def _demo_response(turn: int) -> str:
    """Pre-scripted demo conversation when no API key is set."""
    demos = [
        "I'd love to help you find that photo! Can you tell me — what was the occasion or event? For example, was it a trip, a celebration, or just a regular day?",
        "Great! And do you remember roughly when this was — even just a year or a season like 'summer 2022' is helpful.",
        "Got it. One more thing: do you remember any visual details? Things like who was there, any colors, objects, or where you were — indoors or outdoors?",
        """Thanks, I think I have enough to work with! Here's my search plan:

<search_query>
{
  "occasion": "Goa vacation",
  "approximate_year": "2022",
  "location_context": "Goa, small café",
  "scene_details": ["wooden table", "yellow wall", "outdoor or indoor café"],
  "people_or_subjects": "solo or small group",
  "search_summary": "Café photo from Goa trip around 2022 with warm interior details"
}
</search_query>

Does this sound right? You can correct any detail before I run the search.""",
    ]
    idx = min(turn - 1, len(demos) - 1)
    return demos[idx]


def parse_search_query(text: str) -> "dict | None":
    """Extracts structured search query JSON from model response if present."""
    if "<search_query>" not in text:
        return None
    try:
        start = text.index("<search_query>") + len("<search_query>")
        end   = text.index("</search_query>")
        return json.loads(text[start:end].strip())
    except Exception:
        return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data       = request.get_json()
    session_id = data.get("session_id", "default")
    message    = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Empty message"}), 400

    reply        = chat_with_gemini(session_id, message)
    search_query = parse_search_query(reply)

    # Clean display text (remove the JSON block from visible reply)
    display_reply = reply
    if "<search_query>" in reply:
        display_reply = reply[:reply.index("<search_query>")].strip()
        if search_query:
            display_reply += "\n\n✓ Search plan generated — see the panel on the right."

    return jsonify({
        "reply":        display_reply,
        "search_query": search_query,
    })


@app.route("/reset", methods=["POST"])
def reset():
    data       = request.get_json()
    session_id = data.get("session_id", "default")
    conversations.pop(session_id, None)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"MemoryLens MVP running at http://localhost:{port}")
    print("Set GEMINI_API_KEY env var to enable live Gemini responses.")
    app.run(debug=True, port=port)
