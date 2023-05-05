"""

"""

from typing import Callable
from functools import reduce, wraps

from core import nlp_tools
from core.utils import *


def normalize_one_step_LD_dist(f: Callable) -> Callable:
    @wraps(f)
    def decorated(instance, base_pkg: str, adversarial_pkg: str, *normalized_detectors) -> str:
        if normalized_detectors:
            detector = normalized_detectors
        else:
            detector={} 

        if len(base_pkg) < 4: return f(instance, base_pkg, adversarial_pkg)
        sorted_base_seq = to_sorted_sequence(base_pkg)
        preprocessed_base = '_'.join(sorted_base_seq)

        adversarial_delims = [char for char in adversarial_pkg if char in DELIMITERS]
        adversarial_seq = to_sequence(adversarial_pkg)
        sorted_adversarial_seq = to_sorted_sequence(adversarial_pkg)
        adversarial_sort_map = {token: adversarial_seq.index(token) for token in sorted_adversarial_seq}
        preprocessed_adversarial = '_'.join(sorted_adversarial_seq)

        if len(sorted_adversarial_seq) > len(adversarial_delims) + 1:
            diff = len(sorted_adversarial_seq) - len(adversarial_delims)
            adversarial_delims += [' ' for _ in range(diff)]  
    
        adversarial_processed = adversarial_pkg
        if DL_dist(preprocessed_base, preprocessed_adversarial) == 1:
            for base_token, adversarial_token in zip(sorted_base_seq, sorted_adversarial_seq):
                if base_token != adversarial_token:
                    if abs(len(adversarial_seq[adversarial_sort_map[adversarial_token]]) - len(base_token)) <= 1:
                        adversarial_seq[adversarial_sort_map[adversarial_token]] = base_token
                        adversarial_processed = reduce(lambda base, other: base + other[0] + other[1], zip(adversarial_delims, adversarial_seq[1:]), adversarial_seq[0])
                        detector['1-step-dl'] = True
                    break   

        return f(instance, base_pkg, adversarial_processed, detector)
    return decorated


def normalize_scope(f: Callable) -> Callable:
    @wraps(f)
    def decorated(instance, base_pkg: str, adversarial_pkg: str, *normalized_detectors) -> str:
        split_base_pkg = base_pkg.split('/')
        if len(split_base_pkg) > 1:
            base_pkg_normalized = ''.join(split_base_pkg[1:])
        else:
            base_pkg_normalized = base_pkg

        split_adversarial_pkg = adversarial_pkg.split('/')
        if len(split_adversarial_pkg) > 1:
            adversarial_pkg_normalized = ''.join(split_adversarial_pkg[1:])
        else:
            adversarial_pkg_normalized = adversarial_pkg
        return f(instance, base_pkg_normalized, adversarial_pkg_normalized)
    return decorated


def normalize_delimiters(f: Callable) -> Callable:
    @wraps(f)
    def decorated(instance, base_pkg: str, adversarial_pkg: str, *normalized_detectors) -> str:
        base_replaced = replace_delimiters(base_pkg, '_')
        adversarial_replaced = replace_delimiters(adversarial_pkg, '_')
        return f(instance, base_replaced, adversarial_replaced)
    return decorated


def normalize_sequence_order(f: Callable = None, *, deep: bool = True ) -> Callable:
    def decorator(g):
        @wraps(g)
        def wrapper(instance, base_pkg: str, adversarial_pkg: str, *normalized_detectors) -> str:
            return g(instance, sorted_tokens(base_pkg, deep = deep), sorted_tokens(adversarial_pkg, deep = deep))
        return wrapper
    return decorator(f) if f else decorator


def normalize_grammar(f: Callable) -> Callable:
    @wraps(f)
    def decorated(instance, base_pkg: str, adversarial_pkg: str, *normalized_detectors) -> str:
        base_delims = [char for char in adversarial_pkg if char in DELIMITERS]
        adversarial_delims = [char for char in adversarial_pkg if char in DELIMITERS]
        grammar_checked_base = [nlp_tools.lemmatize(token) for token in to_sequence(base_pkg)]
        grammar_checked_adversarial = [nlp_tools.lemmatize(token) for token in to_sequence(adversarial_pkg)]
        base_processed = reduce(lambda base, other: base + other[0] + other[1], zip(base_delims, grammar_checked_base[1:]), grammar_checked_base[0])
        adversarial_processed = reduce(lambda base, other: base + other[0] + other[1], zip(adversarial_delims, grammar_checked_adversarial[1:]), grammar_checked_adversarial[0])
        return f(instance, base_processed, adversarial_processed)
    return decorated