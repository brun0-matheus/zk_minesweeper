from mine_client import MineClient
from mine_server import MineServer

from flask import Flask, request, jsonify

import random

app = Flask(__name__)
app.secret_key = "TOTALLYRANDOMSECRETKEY"

client = None
server = None
game_state = {}

@app.route("/api/setup", methods=["POST"])
def setup_game():
    zkp_seed = 1337
    grid_size = 10

    global client, server, game_state

    if request.method == "POST":
        data = request.get_json()

        if data:
            if 'seed' in data:
                zkp_seed = int(data['seed'])
            
            if 'grid_size' in data:
                grid_size = int(data['grid_size'])
    
    client = MineClient(n=grid_size, zkp_seed=zkp_seed)
    server = MineServer(n=grid_size, cnt_mines=15, zkp_seed=zkp_seed)

    game_state = {
        'zkp_seed': zkp_seed,
        'grid_size': grid_size,
        'mine_count': 15
    }

    return {"success": True, "game_state": "setup", "data": game_state}, 200

@app.route("/api/init", methods=["POST"])
def init_game():
    data = request.get_json()

    global client, server, game_state

    print(client)

    if not client or not server:
        return {"success": False, "error": "missing call to setup"}, 400

    if not data or 'c_x' not in data or 'c_y' not in data:
        return jsonify({"success": False, "error": "missing initial click coordinates"}), 400
    
    c_x = int(data['c_x'])
    c_y = int(data['c_y'])

    cell_commits, total = server.init_game_creation(ini_click=(c_x, c_y))

    game_state['cell_commits'] = cell_commits
    game_state['commit_total'] = total
    game_state['ini_click'] = (c_x, c_y)

    return {"success": True, "game_state": "init", "data": {}}, 200

@app.route("/api/create_game", methods=["GET", "POST", "PUT"])
def create_game():
    global client, server, game_state
    
    if not client or not server:
        return jsonify({"success": False, "error": "missing call to setup"}), 400
    
    if 'cell_commits' not in game_state:
        return jsonify({"success": False, "error": "must call /api/init first"}), 400

    if request.method == 'GET':
        # Client generates challenge
        challenge = client.verify_game_creation(
            game_state['mine_count'],
            game_state['cell_commits'],
            game_state['commit_total'],
            ini_click=game_state['ini_click']
        )

        return jsonify({
            "success": True,
            "game_state": "challenge_create_game",
            "data": {
                "challenge": hex(challenge)
            }
        }), 200, {"Content-Type": "application/json"}
    
    elif request.method == 'POST':
        data = request.get_json()

        print(data)

        if not data or 'challenge' not in data:
            return jsonify({"success": False, "error": "missing client challenge for game creation"}), 400
        
        chal = int(data['challenge'], 16)
        response = server.finish_proof_total_mine_count(
            chal
        )

        return {
            "success": True,
            "game_state": "challenge_create_game_reply",
            "data": {
                "challenge": hex(chal),
                "response": hex(response)
            }
        }, 200
    
    elif request.method == 'PUT':
        data = request.get_json()

        if not data or 'challenge' not in data or 'response' not in data:
            return jsonify({"success": False, "error": "missing client challenge and server response for game creation"}), 400
        
        chal = int(data['challenge'], 16)
        resp = int(data['response'], 16)

        verified = client.verify_total_mine_count(chal, resp)

        if not verified:
            return {"success": False, "error": "mine count verification failed"}, 400
        
        game_state['mine_count_verified'] = True
        
        return {
            "success": True,
            "game_state": "challenge_create_game_verified",
            "data": {
                "verified": True,
                "mine_count": game_state['mine_count']
            }
        }, 200

@app.route("/api/permute", methods=["POST"])
def apply_permutation():
    """Apply random permutation to shuffle commits."""
    global client, server, game_state
    
    if not client or not server:
        return jsonify({"success": False, "error": "missing call to setup"}), 400
    
    if not game_state.get('mine_count_verified'):
        return jsonify({"success": False, "error": "must verify mine count first"}), 400
    
    # Generate random permutation
    num_commits = len(game_state['cell_commits'])
    permutation = list(range(num_commits))
    random.shuffle(permutation)
    
    # Both apply permutation
    server.finish_game_creation(permutation)
    client.apply_permutation(permutation)
    
    game_state['ready'] = True
    
    return jsonify({
        "success": True,
        "game_state": "ready",
        "data": {
            "permutation_length": num_commits,
        }
    }), 200


@app.route("/api/dig", methods=["POST", "PUT"])
def dig_cell():
    """Dig a cell and return what was found."""
    global client, server, game_state
    
    if not client or not server:
        return jsonify({"success": False, "error": "missing call to setup"}), 400
    
    if not game_state.get('ready'):
        return jsonify({"success": False, "error": "game not ready, complete setup first"}), 400
    
    data = request.get_json()
    if not data or 'x' not in data or 'y' not in data:
        return jsonify({"success": False, "error": "missing x or y coordinate"}), 400
    
    x = int(data['x'])
    y = int(data['y'])
    

    if request.method == 'POST':
        # Server digs
        is_mine, sv_data = server.dig(x, y)
        
        if is_mine:
            secret = sv_data

            game_state['pending_dig'] = {
                'x': x,
                'y': y,
                'is_mine': True,
                'secret': secret
            }
            
            return jsonify({
                "success": True,
                "game_state": "dig_mine", 
                "data": {
                    "mine": True,
                    "x": x,
                    "y": y,
                    "secret": hex(secret)  # Added - shows the revealed secret
                }
            }), 200
        else:
            # Store dig info for verification
            mine_count, proof_commit = sv_data
            
            # Generate challenge immediately
            challenge = client.generate_challenge()
            
            game_state['pending_dig'] = {
                'x': x,
                'y': y,
                'mine_count': mine_count,
                'proof_commit': proof_commit,
                'challenge': challenge
            }
            
            return jsonify({
                "success": True,
                "game_state": "dig_challenge", 
                "data": {
                    "mine": False,
                    "x": x,
                    "y": y,
                    "mine_count": mine_count,
                    "challenge": hex(challenge)  # Added
                }
            }), 200
    elif request.method == 'PUT':
        if 'pending_dig' not in game_state:
            return jsonify({"success": False, "error": "no pending dig to verify"}), 400
        
        if 'is_mine' not in data:
            return jsonify({"success": False, "error": "missing is_mine on data body"}), 400
        
        is_mine = bool(data['is_mine'])
        
        
        pending = game_state['pending_dig']
        
        if is_mine:
            if 'secret' not in data:
                return jsonify({"success": False, "error": "missing dig mine secret"}), 400

            secret = int(data['secret'], 16)

            verified = client.verify_dig_mine(x, y, secret)

            if not verified:
                return jsonify({"success": False, "error": "failed to verify mine"}), 500
            
            del game_state['pending_dig']
            
            return jsonify({
                "success": True,
                "game_state": "dig_mine_verified",
                "data": {
                    "mine": True,
                    "x": x,
                    "y": y,
                    "verified": True,
                    "secret": secret  # Added - shows the revealed secret
                }
            }), 200
        else:
            if 'challenge' not in data:
                return jsonify({"success": False, "error": "missing dig proof challenge"}), 400

            challenge = int(data['challenge'], 16)
            response = server.finish_dig_proof(challenge)

            return jsonify({
                    "success": True,
                    "game_state": "dig_challenge_reply",
                    "data": {
                        "mine": False,
                        "x": x,
                        "y": y,
                        "mine_count": game_state['pending_dig']['mine_count'],
                        "challenge": hex(challenge),
                        "response": hex(response)
                    }
                }), 200

@app.route("/api/verify_dig", methods=["POST"])
def verify_dig_cell():
    """Verify the dig proof for a safe cell."""
    global client, server, game_state
    
    if not client or not server:
        return jsonify({"success": False, "error": "missing call to setup"}), 400
    
    if 'pending_dig' not in game_state:
        return jsonify({"success": False, "error": "no pending dig to verify"}), 400
    
    data = request.get_json()

    if 'challenge' not in data:
        return jsonify({"success": False, "error": "missing dig proof challenge"}), 400
    
    challenge = int(data['challenge'], 16)

    if 'response' not in data:
        return jsonify({"success": False, "error": "missing dig proof challenge"}), 400
    
    response = int(data['response'], 16)
    
    pending = game_state['pending_dig']
    
    # Client verifies
    verified = client.verify_dig_safe(
        pending['x'],
        pending['y'],
        pending['mine_count'],
        pending['proof_commit'],
        challenge,
        response
    )

    if not verified:
        return jsonify({"success": False, "error": "failed to verify mine count"}), 500
    
    del game_state['pending_dig']
    
    return jsonify({
        "success": True,
        "game_state": "dig_challenge_verified",
        "data": {
            "verified": True,
            "x": pending['x'],
            "y": pending['y'],
            "mine_count": pending['mine_count']
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True)