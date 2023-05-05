"""
Plots frequency rank of package tokens
"""

import os.path as osp, os
from icecream import ic
import compress_pickle
from matplotlib import pyplot as plt
from collections import defaultdict
import pandas as pd
import numpy as np
import json
import re

def log(arr, base):
    return np.log(arr) / np.log(base)


PATH = osp.dirname(osp.realpath(__file__))
DATA_PATH = osp.join(PATH, '..', 'data')
TOKEN_DATA = osp.join(DATA_PATH, 'token_sets', 'pkg_tokens.gz')

EXPORT_PATH = osp.join(PATH, '..', 'tmp')

with open(TOKEN_DATA, 'rb') as f:
    TOKENS = compress_pickle.load(f)

num_ptn = re.compile(r'\d+')
all_src = set()

def main():
    # token_hist = defaultdict(int)  # token-pkg occurence to number of tokens with that occurence
    X, Y = list(zip(*sorted(
        [(k, l) for k, v in TOKENS.items() if (l := len(v['src'])) > 1 and not num_ptn.match(k) and len(k) > 1],
        key = lambda item: item[1], reverse = True
    )))
    # for k, v in TOKENS.items():
    #     c = v['count']
    #     src = v['src']
    #     # token_hist[len(src)] += 1
    #     ranked_terms.append((k, len(src)))

    # X, Y = list(zip(*sorted(token_hist.items(), key = lambda item: item[0])))
    # Y = np.array(Y)
    # items = sorted(TOKENS.items(), key = lambda item: item[1]['count'], reverse = True)
    zipf = np.array([Y[0] / i for i in range(1, len(X) + 1)])

    to_export = {'token': [], 'freq': [], 'example_pkgs': []}
    q = "'"
    for i, k in enumerate(X):
        v = TOKENS[k]
        # c = v['count']
        src = v['src']
        for pkg in src: all_src.add(pkg)
        exs = list(src)[:3]
        if i < 20:
            print(f'"{k}": f={len(src)}')
            for s in exs: print(f'\t- {s}')
            if len(src) > 5: print(f'\t- ...')
            print()
        to_export['token'].append(k)
        to_export['freq'].append(len(src))
        to_export['example_pkgs'].append(f'{{{", ".join(q + pkg + q for pkg in exs)}}}')
    
    plt.plot(zipf, label = 'Approx Zipf', color = 'orange', lw = '2')
    plt.plot(Y, label = 'Pkg Tokens', color = 'blue', lw = '2')
    plt.xlabel('Rank')
    plt.yscale('log')
    plt.ylabel('Frequency')
    plt.title('Package Token Freq VS Rank')
    plt.grid(alpha = 0.5, ls = '--')
    plt.legend()
    plt.savefig(osp.join(EXPORT_PATH, 'freq_vs_rank.png'), dpi = 300)
    other_info = {
        'mean_freq': np.mean(Y),
        'median_freq': np.median(Y),
        'stdev_freq': np.std(Y),
        'num_filtered_tokens': len(X),
        'num_src': len(all_src)
    }
    with open(osp.join(EXPORT_PATH, 'info.json'), 'w') as f:
        json.dump(other_info, f, indent=2)

    to_export = pd.DataFrame(to_export)
    to_export.to_excel(osp.join(EXPORT_PATH, 'freq_vs_rank.xlsx'))

if __name__ == '__main__':
    main()