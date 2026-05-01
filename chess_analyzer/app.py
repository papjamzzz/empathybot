import os
import base64
import json
import re
from flask import Flask, render_template, request, jsonify
import anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

ALLOWED_MEDIA_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}


def get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=api_key)


def extract_json(text):
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text.strip())


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    if not file.filename:
        return jsonify({'error': 'Empty file'}), 400

    image_bytes = file.read()
    if not image_bytes:
        return jsonify({'error': 'Empty image file'}), 400

    image_data = base64.standard_b64encode(image_bytes).decode('utf-8')
    media_type = file.content_type
    if not media_type or media_type not in ALLOWED_MEDIA_TYPES:
        media_type = 'image/jpeg'

    try:
        client = get_client()
    except ValueError as e:
        return jsonify({'error': str(e)}), 500

    prompt = (
        "You are a chess expert with perfect vision. Carefully analyze this chess board image.\n\n"
        "Tasks:\n"
        "1. Identify every piece on the board and its exact square (file a-h, rank 1-8)\n"
        "2. Determine whose turn it is (default to White if unclear)\n"
        "3. Generate the correct FEN string for this position\n"
        "4. Determine the single best next move considering tactics, piece safety, and strategy\n\n"
        "IMPORTANT: Respond ONLY with valid JSON — no preamble, no explanation outside the JSON.\n"
        "Use this exact format:\n"
        "{\n"
        '  "fen": "full FEN string (board position only, e.g. rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1)",\n'
        '  "turn": "white",\n'
        '  "move": "move in standard algebraic notation (e.g. Nf3, e4, O-O, Rxe5+)",\n'
        '  "from": "source square lowercase (e.g. g1)",\n'
        '  "to": "destination square lowercase (e.g. f3)",\n'
        '  "explanation": "2-3 sentences explaining why this is the best move"\n'
        "}"
    )

    try:
        client_instance = client
        response = client_instance.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )

        result = extract_json(response.content[0].text)

        for field in ('fen', 'turn', 'move', 'explanation'):
            if field not in result:
                raise ValueError(f"Missing field in AI response: {field}")

        return jsonify({
            'fen': result['fen'],
            'turn': result.get('turn', 'white'),
            'move': result['move'],
            'from': result.get('from', ''),
            'to': result.get('to', ''),
            'explanation': result['explanation']
        })

    except json.JSONDecodeError as e:
        return jsonify({'error': f'Could not parse AI response: {str(e)}'}), 500
    except anthropic.APIError as e:
        return jsonify({'error': f'AI API error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5565))
    app.run(debug=False, port=port, host='0.0.0.0')
