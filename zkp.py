from schnorr import random_point_from_coords, random_point_from_log, schnorr_commit, schnorr_prove, schnorr_challenge, schnorr_verify, Point
from typing import Tuple

''' ZKP based in the Schnorr identification scheme
This can be used to commit to numbers and later prove the sum of any subset of them.

First, create 2 generators g and h. All discrete logs are taken regarding g, and dlog(h) is unknown.

Commit each number v to c = s * g + v * h, where s is a secret nonce (different for each commit).

For a subset, let C be the sum of the commits, S of the secrets and V of the values. The goal is to
prove that C = S * g + V * h without revealing S. This is the same as proving:

C - V*h = S*g

This is the same case of the Schnorr identification scheme, with the public key as (C - V*h) and the private
key as S.
'''

def get_generators(seed: int):
    g = random_point_from_coords('G', seed)
    h = random_point_from_coords('H', seed)
    return g, h

def commit(value: int, g: Point, h: Point) -> Tuple[int, Point]:
    # returns (secret, commit)
    secret, c = random_point_from_log(g)
    c = c + value * h
    return secret, c

def prove_step1(g: Point) -> Tuple[int, Point]:
    # returns (schnorr_secret, schnorr_commit)
    k, u = schnorr_commit(g)
    return k, u

# TODO: implement
def verify_step1(g: Point) -> int:
    return schnorr_challenge(g)

def prove_step2(challenge: int, schnorr_secret: int, sum_secrets: int, g: Point) -> int:
    #public_key = sum_commits - sum_values*h
    return schnorr_prove(challenge, schnorr_secret, sum_secrets, g)

# TODO: implement
def verify_step2(challenge: int, response: int, schnorr_commit: Point, sum_values: int, sum_commits: Point, g: Point, h: Point) -> bool:
    pubkey = sum_commits - sum_values * h

    return schnorr_verify(challenge, response, schnorr_commit, pubkey, g)


if __name__ == '__main__':
    g, h = get_generators(1337)

    vs, ss, cs = [], [], []
    for i in range(10):
        v = 1 << i
        s, c = commit(v, g, h)
        vs.append(v)
        ss.append(s)
        cs.append(c)
    
    for mask in range(1, 2**10):
        V = sum(vs[i] for i in range(10) if ((mask>>i)&1))
        C = sum((cs[i] for i in range(10) if ((mask>>i)&1)), start=0*g)
        S = sum(ss[i] for i in range(10) if ((mask>>i)&1))

        k, u = prove_step1(g)
        # TODO: verifier generates the challenge, should be random
        chal = verify_step1(g)

        ans = prove_step2(chal, k, S, g)


        result = verify_step2(chal, ans, u, V, C, g, h)
        assert result, f"Verification failed for {mask}"

        # TODO: check that verify(chal, u, V, C, g, h) is True
        # also a good ideia to check that changing any of the parameters makes it verify to False

        assert not verify_step2(chal + 1, ans, u, V, C, g, h), "Should fail with wrong challenge"
        assert not verify_step2(chal, ans + 1, u, V, C, g, h), "Should fail with wrong response"
        assert not verify_step2(chal, ans, u + g, V, C, g, h), "Should fail with wrong commit"
        assert not verify_step2(chal, ans, u, V + 1, C, g, h), "Should fail with wrong sum_values"
        assert not verify_step2(chal, ans, u, V, C + g, g, h), "Should fail with wrong sum_commits"
        
    print('Ok')

