"""

"""

from functools import lru_cache
from nltk.stem import WordNetLemmatizer


LEMMATIZER = WordNetLemmatizer()

@lru_cache(2**16)
def lemmatize(target: str) -> str:
    return LEMMATIZER.lemmatize(target)
lemmatize('')  # loads lemmatizer