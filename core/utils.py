
import re
import os.path as osp, os
from functools import reduce
from functools import lru_cache
from typing import List

from pyxdameraulevenshtein import damerau_levenshtein_distance as edit_distance

from icecream import ic
from pipe import traverse

from core.semantic import get_similarity
from core import tokens
from core.segmentation import segment

# statics
PATH = osp.dirname(osp.realpath(__file__))


DELIMITERS = ('-', '_', ' ', '.', '~')
DELIMITIER_PATTERN = re.compile(f'[{"".join(DELIMITERS)}]+')


def replace_delimiters(target: str, replacement: str) -> str:
    return re.sub(DELIMITIER_PATTERN, replacement, target)


def to_sequence(target: str, deep: bool = True) -> List[str]:
    """Splits target string across all delimiters."""
    base_seq = replace_delimiters(target, ' ').split()
    return list([segment(t) for t in base_seq] | traverse) if deep else base_seq


def to_sorted_sequence(target: str, deep = True) -> List[str]:
    """Splits target string across all delimiters."""
    return sorted(to_sequence(target, deep = deep))


@lru_cache(2**16)
def DL_dist(target1: str, target2: str) -> int:
    """Calculates Damerau-Levenshtein distance"""
    return edit_distance(target1, target2)


def sorted_tokens(target: str, deep = True) -> str:
    base_delims = [char for char in target if char in DELIMITERS]
    sorted_base_seq = to_sorted_sequence(target, deep = deep)
    if len(sorted_base_seq) > len(base_delims) + 1:
        diff = len(sorted_base_seq) - len(base_delims)
        base_delims += [' ' for _ in range(diff)]  
    return reduce(lambda base, other: base + other[0] + other[1], zip(base_delims, sorted_base_seq[1:]), sorted_base_seq[0])




