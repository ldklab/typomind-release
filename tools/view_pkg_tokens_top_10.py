"""
Displays top 10 tokens from package tokesn
"""

import os.path as osp, os
from icecream import ic
import pickle


PATH = osp.dirname(osp.realpath(__file__))
DATA_PATH = osp.join(PATH, '..', 'data')
TOKEN_DATA = osp.join(DATA_PATH, 'token_sets', 'pkg_tokens.pkl')


def main():
    with open(TOKEN_DATA, 'rb') as f:
        model = pickle.load(f)
        print('Loaded model...')
        token_dict = {k: v for k, v in model.items() if v['count'] > 1}
        print('Filtered model...')

    
    items = sorted(token_dict.items(), key = lambda item: item[1]['count'], reverse = True)
    print('Sorted model...')

    ic(type(token_dict))
    ic(len(token_dict))

    for k, v in items:
        c = v['count']
        src = v['src']
        print(f'{k}: {c}')
        for s in list(src)[:10]:
            print(f'\t- {s}')
        if len(src) > 10:
            print(f'\t- ...')
        input()


if __name__ == '__main__':
    main()