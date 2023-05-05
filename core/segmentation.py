"""

"""

from typing import Callable, List, Set
from icecream import ic
from functools import lru_cache

from core import nlp_tools, tokens

@lru_cache(2**16)
def segment(target: str) -> List['str']:
    forward_en = _segment_forward(target)
    backward_en = _segment_backward(target)
    forward_pkg = _segment_forward(target, corpus_key_queue = ['packages', 'en'])
    backward_pkg = _segment_backward(target, corpus_key_queue = ['packages', 'en'])

    passes = [forward_en, backward_en, forward_pkg, backward_pkg]
    len_count = [(tuple(s_pass), len(s_pass)) for s_pass in passes]
    count_vals = [l for _, l in len_count]
    len_freq = {l: count_vals.count(l) for l in set(count_vals)}
    max_len_freq = max(len_freq.items(), key = lambda item: item[1])[0]
    ambiguous = len(set(len_count)) > 2
    if ambiguous: return [target]
    viable = [tuple(s_pass) for s_pass in passes if all([s in tokens.corpora['all'] for s in s_pass]) and len(s_pass) == max_len_freq]
    if not viable: return [target]
    candidate_votes = {v: viable.count(v) for v in set(viable)}
    max_votes = max(candidate_votes.values())
    best_candidates = [v for v in viable if candidate_votes[tuple(v)] == max_votes]
    return list(max(best_candidates, key = lambda ss: min([len(s) for s in ss])))


def _segment_forward(
        target: str,
        corpus_key_queue: List[str] = None,
        min_segment_len: int = 2,
        transform: Callable[[str], str] = lambda s, ck: nlp_tools.lemmatize(s) if len(s) > 2 and ck == 'en' else s,
        valid: Callable[[str, Set[str]], bool] = lambda s, c, ck: (len(s) > 2 or ck != 'en') and s in c
    ) -> List[str]:
    """From left to right."""
    if not target: return []
    corpus_key_queue = corpus_key_queue or ['en', 'packages']
    corpus_key = corpus_key_queue.pop(0)
    corpus = tokens.corpora[corpus_key]
    target_len = len(target)
    if target_len <= min_segment_len or target in corpus: return [target]
    for offset in range(target_len - 1):
        if 0 < offset < min_segment_len: continue
        for window in reversed(range(min_segment_len, target_len - offset + 1)):
            frame = target[offset:offset + window]
            if valid(transform(frame, corpus_key), corpus, corpus_key):
                preframe = target[:offset]
                postframe = target[offset + window:]
                if len(postframe) < min_segment_len:
                    frame += postframe
                    postframe = ''
                return ([preframe] if preframe else []) + [frame] + _segment_forward(postframe)
    return [target] if not corpus_key_queue else _segment_forward(target, corpus_key_queue = corpus_key_queue, min_segment_len = min_segment_len, transform = transform, valid = valid)


def _segment_backward(
        target: str,
        corpus_key_queue: List[str] = None,
        min_segment_len: int = 2,
        transform: Callable[[str], str] = lambda s, ck: nlp_tools.lemmatize(s) if len(s) > 2 and ck == 'en' else s,
        valid: Callable[[str, Set[str]], bool] = lambda s, c, ck: (len(s) > 2 or ck != 'en') and s in c
    ) -> List[str]:
    """From right to left."""
    if not target: return []
    corpus_key_queue = corpus_key_queue or ['en', 'packages']
    corpus_key = corpus_key_queue.pop(0)
    corpus = tokens.corpora[corpus_key]
    target_len = len(target)
    if target_len <= min_segment_len or target in corpus: return [target]
    for offset in range(target_len - 1):
        if 0 < offset < min_segment_len: continue
        for window in reversed(range(min_segment_len, target_len - offset + 1)):
            frame = target[-offset - window:-offset or None]
            if valid(transform(frame, corpus_key), corpus, corpus_key):
                preframe = target[-offset:] if offset else ''
                postframe = target[:-offset - window]
                if len(postframe) < min_segment_len:
                    frame = postframe + frame
                    postframe = ''
                return _segment_backward(postframe) + [frame] + ([preframe] if preframe else [])
    return [target] if not corpus_key_queue else _segment_backward(target, corpus_key_queue = corpus_key_queue, min_segment_len = min_segment_len, transform = transform, valid = valid)
