"""

"""

import sys; sys.path.append('.')
import os.path as osp, os

from nltk.corpus import words

import json
import compress_pickle

from icecream import ic

from core import nlp_tools


# statics
PATH = osp.dirname(osp.realpath(__file__))

DATA_PATH = osp.join(PATH, '..', 'data')
PKG_TOKENS_PATH = osp.join(DATA_PATH, 'token_sets', 'pkg_tokens.gz')  
AM_TO_BR_PATH = osp.join(DATA_PATH, 'translations', 'am_to_br.json')

with open(PKG_TOKENS_PATH, 'rb') as f:
    TOKEN_DICT = {k: v for k, v in compress_pickle.load(f).items() if v['count'] >= 100}

with open(AM_TO_BR_PATH, 'r') as f:
    # source: https://github.com/hyperreality/American-British-English-Translator
    AM_TO_BR = json.load(f)

EN_TOKENS = set(words.words()) | set(AM_TO_BR.keys()) | set(AM_TO_BR.values())
EN_TOKENS = {nlp_tools.lemmatize(t) for t in EN_TOKENS}  
PKG_TOKENS = set(TOKEN_DICT.keys())
PKG_TOKEN_SORTED_RANK = sorted(  
        [(k, len(v['src'])) for k, v in TOKEN_DICT.items()],
        key = lambda item: item[1], reverse = True
    )
_max_num_src = max(PKG_TOKEN_SORTED_RANK, key = lambda pair: (lambda key, num_src: num_src)(*pair))[1]
PKG_TOKEN_TO_RANK = {token: num_src / _max_num_src for token, num_src in PKG_TOKEN_SORTED_RANK}
ALL_TOKENS = PKG_TOKENS | EN_TOKENS
TECH_TOKENS = PKG_TOKENS - EN_TOKENS

corpora = {
    'en': EN_TOKENS,
    'packages': PKG_TOKENS,
    'tech': TECH_TOKENS,
    'all': ALL_TOKENS,
}