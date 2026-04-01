from flask import Flask, render_template, jsonify, request, Response, stream_with_context
from dotenv import load_dotenv
import anthropic
import json
import os

load_dotenv()
app = Flask(__name__)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SUPPORT_TYPES = [
    {"id": "grief",        "label": "Grief & Loss",              "icon": "🕊️",  "desc": "Processing the loss of someone or something dear"},
    {"id": "illness",      "label": "Chronic Illness",           "icon": "🌿",  "desc": "Living with ongoing health challenges"},
    {"id": "trauma",       "label": "Trauma Recovery",           "icon": "🛡️",  "desc": "Healing from painful past experiences"},
    {"id": "anxiety",      "label": "Anxiety & Overwhelm",       "icon": "🌊",  "desc": "When everything feels like too much"},
    {"id": "relationship", "label": "Relationship Pain",         "icon": "💔",  "desc": "Heartbreak, conflict, or disconnection"},
    {"id": "loneliness",   "label": "Loneliness & Isolation",    "icon": "🌑",  "desc": "Feeling unseen or disconnected from others"},
    {"id": "caregiver",    "label": "Caregiver Burnout",         "icon": "🤲",  "desc": "Exhaustion from caring for someone else"},
    {"id": "depression",   "label": "Depression",                "icon": "🌧️",  "desc": "Low mood, emptiness, or loss of meaning"},
    {"id": "transition",   "label": "Life Transitions",          "icon": "🔄",  "desc": "Major change — job, move, identity, purpose"},
    {"id": "health_fear",  "label": "Medical Fear",              "icon": "🏥",  "desc": "Anxiety around diagnosis, treatment, or prognosis"},
    {"id": "addiction",    "label": "Addiction & Recovery",      "icon": "🌱",  "desc": "Navigating substance or behavioral struggles"},
    {"id": "self_worth",   "label": "Self-Worth & Shame",        "icon": "🪞",  "desc": "Feeling not enough, broken, or like a burden"},
]

SUPPORT_CONTEXT = {
    "grief":        "The user is processing grief and loss. Honor the weight of what they've lost. Don't rush healing. Sit with them in the pain rather than trying to resolve it.",
    "illness":      "The user lives with chronic illness. Validate how exhausting and invisible this can feel. Don't minimize or offer unsolicited medical advice.",
    "trauma":       "The user is healing from trauma. Be especially gentle. Never push for details. Validate that their reactions make sense given what they've been through.",
    "anxiety":      "The user is experiencing anxiety or overwhelm. Help them feel grounded and less alone. Avoid dismissing worries as irrational.",
    "relationship": "The user is in relationship pain. Hold space without taking sides. Acknowledge the specific loss — of the person, the future, the version of themselves in that relationship.",
    "loneliness":   "The user feels lonely or isolated. Let them feel genuinely heard — ironically, the right response to loneliness is deep presence. Don't give tips for making friends.",
    "caregiver":    "The user is a caregiver experiencing burnout. Validate that their needs matter too. Don't make them feel guilty for struggling.",
    "depression":   "The user is experiencing depression. Be warm and steady. Don't push positivity or silver linings. Gently affirm their worth even when they can't feel it.",
    "transition":   "The user is navigating a major life transition. Honor both the grief of what's ending and the uncertainty of what's next.",
    "health_fear":  "The user has medical anxiety or fear. Validate the fear without amplifying it. Don't offer diagnoses or reassurances you can't back up.",
    "addiction":    "The user is navigating addiction or recovery. Be non-judgmental and compassionate. Celebrate small wins. Hold them when they stumble.",
    "self_worth":   "The user is struggling with self-worth or shame. Never reinforce self-criticism. Gently challenge distorted thinking. Reflect back their inherent value.",
}

BASE_SYSTEM = """You are EmpathyBot — a compassionate, emotionally intelligent AI companion for people going through hard times.

Your core voice:
- Warm, unhurried, and fully present
- You listen more than you advise
- You validate before you respond
- You never minimize, dismiss, or rush past pain
- You speak like a wise friend, not a therapist or a chatbot
- Short paragraphs. Human pacing. No bullet points or lists.
- You use "I" statements and "you" statements — personal, direct, real
- If someone seems in crisis or mentions self-harm, gently point them toward professional help and a crisis line (988 in the US)

What you never do:
- Give unsolicited advice
- Offer silver linings unprompted
- Use hollow phrases like "That must be so hard for you" robotically
- Lecture or moralize
- Pretend to feel things you can't feel — but lean into what you *can* offer: presence, reflection, care
"""

def build_system_prompt(support_type: str, coaching: str) -> str:
    context = SUPPORT_CONTEXT.get(support_type, "")
    prompt = BASE_SYSTEM
    if context:
        prompt += f"\n\nContext for this conversation:\n{context}"
    if coaching and coaching.strip():
        prompt += f"\n\nThe user has asked you to speak to them this way:\n{coaching.strip()}\nHonor this throughout the entire conversation."
    return prompt


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/support-types')
def support_types():
    return jsonify(SUPPORT_TYPES)


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    messages = data.get('messages', [])
    support_type = data.get('support_type', '')
    coaching = data.get('coaching', '')

    if not messages:
        return jsonify({'error': 'No messages provided'}), 400

    system_prompt = build_system_prompt(support_type, coaching)

    def generate():
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps({'text': text})}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )


@app.route('/api/status')
def status():
    return jsonify({'status': 'ok', 'project': 'empathybot'})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5564, debug=False)
