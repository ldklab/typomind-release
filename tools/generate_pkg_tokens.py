"""
Takes in csv of python and npm packages and generates tokenized dictionary.
"""

import os.path as osp, os
import re
from icecream import ic
import pandas as pd
import wordsegment as ws; ws.load()
from tqdm import tqdm
from collections import defaultdict
import psutil
import compress_pickle
import time


PATH = osp.dirname(osp.realpath(__file__))
DATA_PATH = osp.join(PATH, '..', 'data')
PY_DATA = osp.join(DATA_PATH, 'token_sets', 'gen', 'python-packages-with-downloads.csv')
NPM_DATA = osp.join(DATA_PATH, 'token_sets', 'gen', 'npm-package-list.csv')

DELIMITERS = ('-', '_', ' ', '.', '~', '@', '/')
DELIMITIER_PATTERN = re.compile(f'[{"".join(DELIMITERS)}]+')


class Timer:
    """This context manager allows timing blocks of code."""
    def __enter__(self) -> None:
        self._timer = time.time()
        return self

    def __exit__(self, *args: list) -> None:
        self.elapsed = time.time() - self._timer


def numrepl(match):
    return match.group() + ' '

def replace_delimiters(target: str, replacement: str) -> str:
    delim_pass = re.sub(DELIMITIER_PATTERN, replacement, target)
    num_pass = re.sub(r'[0-9]+', numrepl, delim_pass)
    return num_pass


def to_sequence(target: str) -> list[str]:
    """Splits target string across all delimiters."""
    return replace_delimiters(target, ' ').split()


def get_mem_usage(precision: int = 2) -> float:
    """Returns current process' memory usage in MB."""
    process = psutil.Process(os.getpid())
    return round(process.memory_info().rss / 1000000, precision)


def get_packages():
    py_data = pd.read_csv(PY_DATA).dropna()
    npm_data = pd.read_csv(NPM_DATA).dropna()
    py_packages = set(py_data.loc[:, 'project'])
    npm_packages = set(npm_data.iloc[:, 0]) | {npm_data.columns[0]}
    return py_packages | npm_packages


def main():
    token_dict = defaultdict(lambda: {'count': 0, 'src': set(), 'is_segment': False})
    packages = get_packages()
    
    start_mem = get_mem_usage()

    def get_data_size():
        return get_mem_usage() - start_mem

    with Timer() as timer:
        for i, p in enumerate(tqdm(packages)):
            p_seq = [s.lower() for s in to_sequence(p)]
            for t in p_seq:
                if len(t) > 1:
                    segments = [s.lower() for s in ws.segment(t)]
                    for s in segments:
                        token_dict[s]['count'] += 1
                        token_dict[s]['src'].add(p)
                        if s != t:
                            token_dict[s]['is_segment'] = True
                    token_dict[t]['count'] += 1
                    token_dict[t]['src'].add(p)
    
    ic(get_data_size())
    ic(timer.elapsed)

    with open(osp.join(DATA_PATH, 'token_sets', 'pkg_tokens.gz'), 'wb') as f:
        compress_pickle.dump(dict(token_dict), f, compression = 'gzip')


if __name__ == '__main__':
    main()