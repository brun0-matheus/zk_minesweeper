from typing import Tuple
import secrets

from zkp import get_generators, commit, prove_step1, prove_step2
from utils import apply_permutation

class MineServer:
    def __init__(self, n: int, cnt_mines: int, zkp_seed: int) -> None:
        self.n = n
        self.g, self.h = get_generators(zkp_seed)
        self.cnt_mines = cnt_mines

    def init_game_creation(self, ini_click: Tuple[int, int]) -> Tuple[List[Point], Point]:
        # returns cell commits and a commit to prove the total mine count
        self.death_count = 0
        self.dig_secret = None

        n = self.n
        g = self.g
        h = self.h

        self.dug_mines = [[False]*n for _ in range(n)]
        self.cnt_dug_mines = 0
        for i in range(max(0, ini_click[0]-1), min(n, ini_click[0]+2)):
            for j in range(max(0, ini_click[1]-1), min(n, ini_click[1]+2)):
                self.dug_mines[i][j] = True
                self.cnt_dug_mines += 1

        cnt_cells = n*n - self.cnt_dug_mines
        self.ini_mines = [0]*cnt_cells
        tmp = list(range(cnt_cells))
        for _ in range(self.cnt_mines):
            pos = secrets.choice(tmp)
            tmp.remove(pos)
            self.ini_mines[pos] = 1

        self.ini_secs_commits = [commit(v, g, h) for v in self.ini_mines]
        self.secret_total_mine, commit_total_mine = prove_step1(self.g)

        return [c for _, c in self.ini_secs_commits], commit_total_mine

    def finish_proof_total_mine_count(self, challenge: int) -> int:
        sum_commits = sum((c for _, c in self.ini_secs_commits), start=0*self.g)
        sum_secrets = sum((s for s, _ in self.ini_secs_commits))
        return prove_step2(challenge, self.secret_total_mine, sum_secrets, self.g)

    def finish_game_creation(self, permutation: List[int]) -> None:
        self.ini_secs_commits = apply_permutation(self.ini_secs_commits, permutation)
        self.ini_mines = apply_permutation(self.ini_mines, permutation)

        self.commits = [[None]*self.n for _ in range(self.n)]
        self.grid = [[0]*self.n for _ in range(self.n)]

        for i in range(self.n):
            for j in range(self.n):
                if self.dug_mines[i][j]:
                    self.commits[i][j] = (0, 0*self.g)
                    continue 
                self.grid[i][j] = self.ini_mines.pop()
                self.commits[i][j] = self.ini_secs_commits.pop()
        
    def dig(self, i: int, j: int):
        # returns is_mine, data
        # if a mine was selected, then the server simply opens the commit, so data is (secret[i][j])
        # otherwise, then the server returns the mine count in neighbooring cells and a proof commit, so
        #      data is (adj_mine_count, proof_commit)

        assert self.dig_secret is None

        if self.grid[i][j]:
            self.death_count += 1
            return True, self.commits[i][j][0]

        self.dig_secret, dig_commit = prove_step1(self.g)
        self.dig_secrets_sum = 0
        mine_count = 0
        for x in range(max(i-1, 0), min(i+2, self.n)):
            for y in range(max(j-1, 0), min(j+2, self.n)):
                mine_count += self.grid[x][y]
                self.dig_secrets_sum += self.commits[x][y][0]

        if not self.dug_mines[i][j]:
            self.dug_mines[i][j] = 1
            self.cnt_dug_mines += 1

        return False, (mine_count, dig_commit)

    def finish_dig_proof(self, challenge: int) -> int:
        return prove_step2(challenge, self.dig_secret, self.dig_secrets_sum, self.g)

    def has_won(self) -> bool:
        return self.cnt_dug_mines + self.cnt_mines == self.n**2

