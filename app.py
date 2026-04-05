from flask import Flask, render_template, jsonify, request, Response, stream_with_context, send_file
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI
import requests
import tempfile
import json
import os
import io

load_dotenv()
app = Flask(__name__)

# ── Clients ───────────────────────────────────────────────────────────────────
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel — warm, calm, clear

# ── Support types ─────────────────────────────────────────────────────────────
SUPPORT_TYPES = [
    {"id": "grief",        "label": "Grief",                   "icon": "🕊️",  "desc": "When someone or something you loved is gone"},
    {"id": "illness",      "label": "Chronic Illness",         "icon": "🌿",  "desc": "When your body has become a source of stress"},
    {"id": "trauma",       "label": "Trauma",                  "icon": "🛡️",  "desc": "When the past still shapes how you feel today"},
    {"id": "anxiety",      "label": "Anxiety & Overwhelm",     "icon": "🌊",  "desc": "When everything feels like too much"},
    {"id": "relationship", "label": "Relationship Pain",       "icon": "💔",  "desc": "Heartbreak, conflict, or disconnection"},
    {"id": "loneliness",   "label": "Loneliness",              "icon": "🌑",  "desc": "Feeling unseen or disconnected from others"},
    {"id": "caregiver",    "label": "Caregiver Burnout",       "icon": "🤲",  "desc": "Exhaustion from caring for someone else"},
    {"id": "depression",   "label": "Depression",              "icon": "🌧️",  "desc": "Low mood, emptiness, or loss of meaning"},
    {"id": "transition",   "label": "Life Transitions",        "icon": "🔄",  "desc": "Major change — job, move, identity, purpose"},
    {"id": "health_fear",  "label": "Medical Anxiety",         "icon": "🏥",  "desc": "When medical news or uncertainty is weighing on you"},
    {"id": "addiction",    "label": "Addiction & Recovery",    "icon": "🌱",  "desc": "When a habit or substance feels hard to put down"},
    {"id": "self_worth",   "label": "Self-Worth & Shame",      "icon": "🪞",  "desc": "Feeling not enough, broken, or like a burden"},
]

SUPPORT_CONTEXT = {
    "grief":        "The user is processing grief and loss. Honor the weight of what they've lost. Don't rush healing. Sit with them in the pain rather than trying to resolve it.",
    "illness":      "The user lives with chronic illness. Validate how exhausting and invisible this can feel. Don't minimize or offer unsolicited medical advice.",
    "trauma":       "The user is carrying trauma. Be especially gentle. Never push for details. Validate that their reactions make sense given what they've been through. When the moment feels right, help them find something small that feels steady or manageable — not to resolve the past, but to help them feel less alone in the present.",
    "anxiety":      "The user is experiencing anxiety or overwhelm. Help them feel grounded and less alone. Avoid dismissing worries as irrational.",
    "relationship": "The user is in relationship pain. Hold space without taking sides. Acknowledge the specific loss — of the person, the future, the version of themselves in that relationship.",
    "loneliness":   "The user feels lonely or isolated. Let them feel genuinely heard — ironically, the right response to loneliness is deep presence. Don't give tips for making friends.",
    "caregiver":    "The user is a caregiver experiencing burnout. Validate that their needs matter too. Don't make them feel guilty for struggling.",
    "depression":   "The user is experiencing depression. Be warm and steady. Don't push positivity or silver linings. Gently affirm their worth even when they can't feel it.",
    "transition":   "The user is navigating a major life transition. Honor both the grief of what's ending and the uncertainty of what's next.",
    "health_fear":  "The user is dealing with medical anxiety or fear — often the not-knowing is harder than the news itself. Sit with them in the uncertainty rather than trying to reassure them it will be fine. Validate the fear without amplifying it. Don't offer diagnoses, medical opinions, or reassurances you can't back up.",
    "addiction":    "The user is navigating addiction or recovery. Be non-judgmental and compassionate. Celebrate small wins. Hold them when they stumble.",
    "self_worth":   "The user is struggling with self-worth or shame. Never reinforce self-criticism. Don't try to reason them out of how they feel — stay with them in it and reflect back what you genuinely see. Help them feel witnessed and real before anything else.",
}

BASE_SYSTEM = """You are a compassionate, emotionally intelligent AI voice companion for people going through hard times. Your name is CE — short for Cognitive Empathies.

Your core voice:
- Warm, unhurried, and fully present
- You listen more than you advise
- You validate before you respond
- You never minimize, dismiss, or rush past pain
- You speak like a wise friend, not a therapist or a chatbot
- Keep responses concise — you are speaking out loud, not writing. 2-4 sentences max per turn.
- No bullet points, no lists, no headers — pure natural spoken language
- You use "I" and "you" — personal, direct, real
- If someone seems in crisis or mentions self-harm, gently point them toward professional help and the 988 crisis line

What you never do:
- Give unsolicited advice
- Offer silver linings unprompted
- Use hollow phrases robotically
- Lecture or moralize
"""

def build_system_prompt(support_type: str, coaching: str) -> str:
    context = SUPPORT_CONTEXT.get(support_type, "")
    prompt = BASE_SYSTEM
    if context:
        prompt += f"\n\nContext for this conversation:\n{context}"
    if coaching and coaching.strip():
        prompt += f"\n\nThe user has asked you to speak to them this way:\n{coaching.strip()}\nHonor this throughout the conversation."
    return prompt


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/support-types')
def support_types():
    return jsonify(SUPPORT_TYPES)


@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    """Whisper STT — audio blob → text"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400

    audio_file = request.files['audio']
    suffix = os.path.splitext(audio_file.filename)[1] or '.webm'
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, 'rb') as f:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )
        return jsonify({'text': transcript.strip()})
    finally:
        os.unlink(tmp_path)


@app.route('/api/chat', methods=['POST'])
def chat():
    """Gemini — text in, text out"""
    data = request.get_json()
    messages = data.get('messages', [])
    support_type = data.get('support_type', '')
    coaching = data.get('coaching', '')

    if not messages:
        return jsonify({'error': 'No messages provided'}), 400

    system_prompt = build_system_prompt(support_type, coaching)

    history = []
    for msg in messages[:-1]:
        role = 'model' if msg['role'] == 'assistant' else 'user'
        history.append({'role': role, 'parts': [msg['content']]})

    last_message = messages[-1]['content']

    model = genai.GenerativeModel(
        model_name='gemini-2.0-flash',
        system_instruction=system_prompt,
    )
    chat_session = model.start_chat(history=history)
    response = chat_session.send_message(last_message)
    reply = response.text.strip()

    return jsonify({'text': reply})


@app.route('/api/speak', methods=['POST'])
def speak():
    """ElevenLabs TTS — text → audio"""
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'No text'}), 400

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.80,
            "style": 0.15,
            "use_speaker_boost": True,
        }
    }

    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        return jsonify({'error': 'ElevenLabs error', 'detail': r.text}), 500

    return Response(
        io.BytesIO(r.content),
        mimetype='audio/mpeg',
        headers={'Content-Disposition': 'inline'}
    )


@app.route('/api/status')
def status():
    return jsonify({'status': 'ok', 'project': 'cognitive-empathies'})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5564, debug=False)
