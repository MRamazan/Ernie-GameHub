from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from gradio_client import Client
import os
import random
app = Flask(__name__, static_folder='static')
CORS(app)

client = Client("https://baidu-simple-ernie-bot-demo.hf.space/")


def check_winner(board, player):
    wins = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]
    return any(board[a] == board[b] == board[c] == player for a, b, c in wins)


def board_full(board):
    return all(cell != " " for cell in board)


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

variation_id = random.randint(0,10000)
@app.route('/api/ai-move', methods=['POST'])
def ai_move():
    global variation_id
    data = request.json
    board = data['board']

    # random playstyle will be choosed for randomness
    PLAYSTYLES = [
        "Aggressive: prioritize creating winning threats over blocking when outcomes are equal",
        "Defensive: prioritize blocking opponent threats and avoiding risky positions",
        "Balanced: mix offense and defense depending on board state",
        "Center-focused: prefer center control when possible",
        "Corner-focused: prefer corner plays to create diagonal threats",
        "Trap-oriented: prefer moves that create future forks or traps",
        "Safe-play: avoid complex positions and prefer simple outcomes",
        "Pressure-based: prefer moves that force the opponent to respond",
    ]
    playstyle = random.choice(PLAYSTYLES)

    prompt = f"""Game variation id: {variation_id}
    
You are playing Tic Tac Toe as O.

RULES:
- You are O, the opponent is X
- Players take turns placing one mark
- A player wins if they place 3 of their own marks in the same row, column, or diagonal
- Play legally
- Do NOT choose an occupied cell
- If multiple equally optimal moves exist, choose one randomly
- Return ONLY a single number between 0 and 8
- No explanation

PLAY STYLE:
- {playstyle}

OBJECTIVE:
- Win the game

Board positions:
0 | 1 | 2
---------
3 | 4 | 5
---------
6 | 7 | 8

Current board:
{board}"""

    for _ in range(3):
        try:
            result = client.predict(
                query=prompt,
                chatbot=[],
                file_url=[],
                search_state=False,
                api_name="/partial"
            )

            ai_response = result[0][-1]["content"].strip()

            if ai_response.isdigit():
                move = int(ai_response)
                if 0 <= move <= 8 and board[move] == " ":
                    board[move] = "O"

                    winner = None
                    if check_winner(board, "O"):
                        winner = "O"
                        variation_id = random.randint(1, 10000)

                    elif board_full(board):
                        winner = "draw"
                        variation_id = random.randint(1, 10000)
                    else:
                        variation_id = random.randint(1, 10000)

                    return jsonify({
                        "success": True,
                        "move": move,
                        "board": board,
                        "winner": winner
                    })
        except Exception as e:
            print(f"Error: {e}")
            continue

    return jsonify({"success": False, "error": "AI failed to make a valid move"})


import random
import json
import re
from flask import jsonify

variation_seed = random.randint(0, 1_000_000)

@app.route('/api/trivia', methods=['GET'])
def trivia():
    CATEGORIES = [
        "psychology misconceptions",
        "everyday cognitive biases",
        "personality myths",

        "ancient Greek history",
        "ancient Roman history",
        "medieval Europe myths",
        "Chinese imperial history",
        "Japanese feudal history",
        "Viking age myths",
        "World War misconceptions",
        "famous historical lies",

        "space and astronomy misconceptions",
        "AI and internet myths",

        "philosophy misconceptions",
        "ancient philosophy myths",

        "movie myths",
        "anime"
        "anime misconceptions",
        "anime characters"
        "video game myths",
        "famous quote misattributions",
        "pop culture false beliefs",

        "Greek mythology myths",
        "Norse mythology myths",
        "myths people think are historical facts",
    ]

    CONFIDENCE_TRAPS = [
        "obviously true sounding",
        "commonly repeated but wrong",
        "half-true statement",
        "confidently taught in school",
        "sounds logical but false",
        "pop culture reinforced belief"
    ]

    global variation_seed

    category = random.choice(CATEGORIES)

    confidence_trap = random.choice(CONFIDENCE_TRAPS)

    prompt = f"""
    Generate a "Two Truths and One Lie" question in the category: {category}.

    Focus on widely believed myths, misconceptions, or pop culture misunderstandings.
    The goal is to trigger a strong "I was confident about this" reaction.

    CONFIDENCE TRAP STYLE:
    The FALSE statement must strongly match this trap:
    - {confidence_trap}

    RULES: 
    - Create THREE statements
    - EXACTLY one statement must be false, and other 2 statements MUST be exactly true
    - Avoid academic or technical facts
    - The lie should NOT be easily spotted by tone alone

    VARIATION SEED: {variation_seed}
    IMPORTANT:
    - This seed forces variation. Do NOT reuse common trivia examples.

    OUTPUT FORMAT:
    Return ONLY a STRICTLY VALID JSON object.
    NO explanations outside JSON.

    Exact format:
    {{
      "statements": ["statement1", "statement2", "statement3"],
      "lie": index of the false statement (0,1,2),
      "explanation": "Briefly explain why the false statement is wrong and state the correct information."
    }}
    """

    try:
        result = client.predict(
            query=prompt,
            chatbot=[],
            file_url=[],
            search_state=False,
            api_name="/partial"
        )

        response = result[0][-1]["content"].strip()
        print(response)

        json_match = re.search(r'\{[\s\S]*\}', response)
        print(json_match)
        if json_match:
            trivia_data = json.loads(json_match.group())
            return jsonify(trivia_data)

        return jsonify({"error": "Failed to parse response"})
    except Exception as e:
        return jsonify({"error": str(e)})



@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, port=5000)