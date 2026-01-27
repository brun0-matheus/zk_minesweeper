from mine_client import MineClient
from mine_server import MineServer

from flask import Flask, request

app = Flask(__name__)
app.secret_key = "TOTALLYRANDOMSECRETKEY"

client = None
server = None

@app.route("/api/setup", methods=["POST"])
def setup_game():
    zkp_seed = 1337
    grid_size = 10

    global client, server

    if request.method == "POST":
        data = request.get_json()

        if data:
            if 'seed' in data:
                zkp_seed = int(data['seed'])
            
            if 'grid_size' in data:
                grid_size = int(data['grid_size'])
    
    client = MineClient(n=grid_size, zkp_seed=zkp_seed)
    server = MineServer(n=grid_size, cnt_mines=15, zkp_seed=zkp_seed)

    return {"success": True, "game_state": "setup"}, 200

@app.route("/api/init", methods=["POST"])
def init_game():
    data = request.get_json()

    global client, server

    print(client)

    if not client or not server:
        return {"success": False, "error": "missing call to setup"}, 400

    if data:
        c_x = int(data['c_x'])
        c_y = int(data['c_y'])

        cell_commits, total = server.init_game_creation(ini_click=(c_x, c_y))

        challenge = client.verify_game_creation(15, cell_commits, total, ini_click=(c_x, c_y))

        response = server.finish_proof_total_mine_count(challenge)

        client_res = client.verify_total_mine_count(challenge, response)

        if not client_res:
            return {"success": False, "error": "error verifying total mine count"}, 400
        
        import random
        permutation = list(range(len(cell_commits)))
        random.shuffle(permutation)
        server.finish_game_creation(permutation)
        client.apply_permutation(permutation)

        return {"success": True, "game_state": "init"}, 200
    else:
        return {"success": False, "error": "missing initial click"}, 400

@app.route("/api/dig", methods=["POST"])
def dig_mine():
    data = request.get_json()

    global client, server

    if not client or not server:
        return {"success": False, "error": "missing call to setup"}, 400
    
    if data:
        x = int(data['x'])
        y = int(data['y'])

        is_mine, sv_data = server.dig(x, y)
        if is_mine:
            secret = sv_data
            verify_results = client.verify_dig_mine(x, y, secret)
            if verify_results:
                return {"success": True, "data": {"is_mine": True}}, 200
            else:
                return {"success": False, "error": "failed to verify if client dug mine"}, 500
        else:
            mine_count, proof_commit = sv_data
            challenge = client.generate_challenge()
            response = server.finish_dig_proof(challenge)
            is_count_valid = client.verify_dig_safe(x, y, mine_count, proof_commit, challenge, response)

            if is_count_valid:
                return {"success": True, "data": {"mine_count": mine_count}}, 200
            else:
                return {"success": False, "error": "failed to verify mine count"}, 500

if __name__ == '__main__':
    app.run()