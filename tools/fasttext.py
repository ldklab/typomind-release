import pandas as pd
import numpy as np
import re
from tqdm import tqdm
import fasttext
import nltk

from gensim.models import KeyedVectors

try: import pry
except ModuleNotFoundError: pass


def load_fasttext():
    model = KeyedVectors.load_word2vec_format('../data/crawl-300d-2M-subword/crawl-300d-2M-subword.vec')
    model.save('fasttext-vectors.kv')
    return model

load_fasttext()
