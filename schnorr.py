from fastecdsa.curve import P256
from fastecdsa.point import Point
from hashlib import sha256
from typing import Optional, Tuple
import secrets


def _get_point_from_x(x: int) -> Optional[Point]:
    a, b, p = P256.a, P256.b, P256.p
    x %= p
    y2 = (pow(x, 3, p) + a*x + b) % p

    y = pow(y2, (p+1)//4, p)
    if pow(y, 2, p) != y2:
        #assert pow(y2, (p-1)//2, p) == p-1
        return None

    y = min(y, p-y)
    return Point(x,y,curve=P256)

def random_point_from_coords(name: str, seed: int) -> Point:
    ini_str = f'{name}|{seed}|'.encode()
    i = 0
    while True:
        s = ini_str + str(i).encode()
        x = int.from_bytes(sha256(s).digest(), 'big')
        pt = _get_point_from_x(x)

        if pt is not None:
            return pt
        i += 1

def random_point_from_log(g: Point) -> Tuple[int, Point]:
    # returns x, pt = x*g
    x = secrets.randbelow(g.curve.q)
    return x, x*g

def schnorr_commit(g: Point) -> Tuple[int, Point]:
    return random_point_from_log(g)

def schnorr_challenge(g: Point) -> int:
    return secrets.randbelow(g.curve.q)

def schnorr_prove(challenge: int, commit_dlog: int, private_key: int, g: Point) -> int:
    # returns dlog(COMMIT + challenge*PUBLIC_KEY)
    return (commit_dlog + challenge*private_key) % g.curve.q

def schnorr_verify(challenge: int, response: int, commit: Point, public_key: Point, g: Point) -> bool:
    left_side = g * response
    right_side = commit + challenge * public_key
    return left_side == right_side

