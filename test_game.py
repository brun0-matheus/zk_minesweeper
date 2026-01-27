from mine_client import MineClient
from mine_server import MineServer

ZKP_SEED = 1337
GRID_SIZE = 10

# Setup phase
client = MineClient(n=GRID_SIZE, zkp_seed=ZKP_SEED)
server = MineServer(n=GRID_SIZE, cnt_mines=15, zkp_seed=ZKP_SEED)

# 1. Server initializes game
cell_commits, commit_total = server.init_game_creation(ini_click=(0, 0))

print(f"Number of cell commits: {len(cell_commits)}")
print(f"Expected: {GRID_SIZE*GRID_SIZE - server.cnt_dug_mines}")

# 2. Client verifies and generates challenge
challenge = client.verify_game_creation(15, cell_commits, commit_total, ini_click=(0, 0))

# 3. Server proves total mine count
response = server.finish_proof_total_mine_count(challenge)

# 4. Client verifies total mine count
assert client.verify_total_mine_count(challenge, response)

# 5. Client generates random permutation and both apply it
import random
permutation = list(range(len(cell_commits)))
random.shuffle(permutation)
server.finish_game_creation(permutation)
client.apply_permutation(permutation)

# Gameplay: Dig a cell
is_mine, data = server.dig(5, 5)

if is_mine:
    # Server reveals secret
    secret = data
    assert client.verify_dig_mine(5, 5, secret), f"Failed to verify mine at 5,5, server returned {secret}"
else:
    # Server provides proof of neighboring mine count
    mine_count, proof_commit = data
    challenge = client.generate_challenge()
    response = server.finish_dig_proof(challenge)
    is_count_valid = client.verify_dig_safe(5, 5, mine_count, proof_commit, challenge, response)
    assert is_count_valid, f"Failed to verify if neighboring mine count at 5,5 is valid, server returned {is_count_valid}"