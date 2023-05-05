"""
Some basic maps for converting between numerical label and standardized string categorization.
"""

from typing import Iterable


def gen_category_to_label_base(categories: Iterable) -> str:
    """Used to construct keys/ template for raw_category_to_label dict."""
    cat_to_label = {category: (None,) for category in set(categories)}
    return '{\n' + ',\n'.join([f'\t\'{k}\': {v}' for k, v in cat_to_label.items()]) + '\n}'

label_to_std_category = {  # numerical label to standardized str category
    1: '1-step D-L dist',
    2: 'homographic replacement',
    3: 'delimiter modification',
    4: 'prefix/ suffix augmentation',
    5: 'alternate spelling',
    6: 'simplification',
    7: 'sequence reordering',
    8: 'semantic substitution',
    9: 'asemantic substitution',
    10: 'grammatical substitution',
    11: 'scope confusion',
    # 12: 'familiar term abuse',
    13: 'homophonic similarity',
}

std_category_to_label = {v: k for k, v in label_to_std_category.items()}  # inverted label_to_std_category

raw_category_to_label = {  # keys include all unique category desc which are mapped to appropriate numerical labels
    'Homographic replacement + Delimiter modification': (2, 3),
    '1 Step Damerau/Levenshtein Distance': (1,),
    'Alternate spelling': (5,),
    'Prefix/suffix augmention + 1-step Damerau/Levenshtein distance': (4, 1),
    '1-step Damerau/Levenshtein distance + 1-step Damerau/Levenshtein distance': (1, 1),
    'Sequence reordering': (7,),
    'Prefix/suffix augmentation + 1-step Damerau/Levenshtein distance': (4, 1),
    'Semantic substitution': (8,),
    'Asemantic substitution + Delimiter modification': (9, 3),
    'Prefix/suffix augmentation': (4,),
    'Sequence reordering + Delimiter modification': (7, 3),
    'Grammatical substitution': (10,),
    'Delimiter modification + homophonic similarity': (3, 13),
    'Semantic Substitution + Delimiter modification + Simplification': (8, 3, 6),
    'Homographic replacement': (2,),
    'Sequence reordering + Prefix/suffix augmentation': (7, 4),
    'Simplification': (6,),
    '1-Step Damerau/Levenshtein Distance + Prefix/Suffix Augmentation': (1, 4),
    'Simplification + Prefix/suffix augmentation': (6, 4),
    'delimiter modification': (3,),
    'Simplification + 1-step Damerau/Levenshtein distance': (6, 1),
    'Delimiter modification + 1-step D/L distance+ 1-step D/L distance': (3, 1, 1),
    'Scope confusion': (11,),
    'Delimiter modification + 1-step Damerau/Levenshtein distance': (3, 1),
    'Semantic substitution + Simplification + Delimiter modification': (8, 6, 3),
    'Delimiter modification + Grammatical substitution': (3, 10),
    'Homophonic similarity': (13,),
    'Asemantic substitution': (9,),
    '1-step D/L distance + 1-step D/L distance': (1, 1),
    '1-step Damerau/Levenshtein distance': (1,),
    'Prefix/Suffix augmentation': (4,),
    'Delimitier Modification': (3,),
    'Semantic substitution + Delimiter modification': (8, 3),
    'Familiar term abuse': (12,),
    'Delimiter modification': (3,),
    '1- step Damerau/Levenshtein Distance': (1,),
    'Delimiter-Modification + 1-step Damerau/Levenshtein Distance': (3, 1)
}

for v in raw_category_to_label.values():
    assert isinstance(v, tuple)