from typing import List

def apply_permutation(lst: List, perm: List[int]) -> List:
    assert len(lst) == len(perm)
    
    tmp = [None] * len(lst)
    for i in range(len(lst)):
        nxt = perm[i]
        tmp[nxt] = lst[i]

    return tmp

