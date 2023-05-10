"""
READY TO TEST:
    - 1-step D-L dist (1)
    - Delimiter modification (3)
    - prefix/ suffix augmentation (4)
    - alternate spelling (5)
    - simplification (6)
    - Sequence reordering (7)
    - grammatical substitution (10)
    - homophonic similarity (13)  # NOTE: many cases of false positive may be ambiguous labeling errors
    - asemantic substitution (9)
    - scope confusion (11)
    - semantic substitution (8) # NOTE: depends on segmentation, needs to be tested after update   
    - homographic replacement (2) 

OMITTED:
    - familiar term abuse (12)

Notes:
    - potentially need to consider precedence of rules, and make current categories globally accessible

"""

from abc import ABCMeta, abstractmethod
from faulthandler import is_enabled
from itertools import permutations
from jellyfish import soundex, metaphone
from typing import List, Dict

from icecream import ic

from core import utils, homographic
from core import nlp_tools
from core import tokens
from core import normalizers
from core import semantic
try: import pry
except ModuleNotFoundError: pass

class DetectorBase(metaclass = ABCMeta):
    cls_registry = {}
    enabled_inst_registry = set()
    scoped_inst_registry = set()

    def __init_subclass__(cls) -> None:
        if not hasattr(cls, 'enabled'):
            cls.enabled = True
        if not hasattr(cls, 'is_scoped'):
            cls.is_scoped = False
        if not hasattr(cls, 'name'):
            raise TypeError(f'{cls} needs a static "name" attribute')
        if not hasattr(cls, 'key'):
            raise TypeError(f'{cls} needs a static "key" attribute')
        if cls.key in DetectorBase.cls_registry:
            raise TypeError(f'"{cls.key}" already mapped to {DetectorBase.cls_registry[cls.key]}')
        DetectorBase.cls_registry[cls.key] = cls
        if cls.enabled: DetectorBase.enabled_inst_registry.add(cls())
        if cls.is_scoped: DetectorBase.scoped_inst_registry.add(cls())

    @abstractmethod
    def __call__(self, base_pkg: str, adversarial_pkg: str, *normalized_detectors) -> int:
        raise NotImplementedError

def is_unscoped(base_pkg: str, adversarial_pkg: str):
    bp = base_pkg.split('/')
    ap = adversarial_pkg.split('/')

    if len(bp) == 1 and len(ap) ==1:
        return True
    else:
        return False


def classify_typosquat(base_pkg: str, adversarial_pkg: str) -> Dict[str, int]:
    if not base_pkg or not adversarial_pkg or len(base_pkg) == 0  or len(adversarial_pkg) == 0: return {}
    if len(base_pkg) > 35 or len(adversarial_pkg) > 35: return{}
    if is_unscoped(base_pkg, adversarial_pkg):
        detector_count = {(d.key, d.name): d(base_pkg, adversarial_pkg) for d in DetectorBase.enabled_inst_registry}
    else:
        detector_count = {(d.key, d.name): d(base_pkg, adversarial_pkg) for d in DetectorBase.scoped_inst_registry}
    return {_: c for _, c in detector_count.items() if c}

class AsemanticSubstitution(DetectorBase):
    key, name = (9, 'asemantic substitution')
    
    @normalizers.normalize_one_step_LD_dist
    @normalizers.normalize_delimiters
    def __call__(self, base_pkg: str, adversarial_pkg: str, *normalized_detectors) -> int:
        # if len(normalized_detectors) > 0 and '1-step-dl' in normalized_detectors[0].keys():
        #     print(f"{base_pkg}, {adversarial_pkg}: 1-step-dl + asemantic substitution")

        is_asemantic = semantic.check_asemantic(base_pkg, adversarial_pkg)

        return 1 if is_asemantic == True else 0

class HomographicReplacement(DetectorBase):
    key, name = (2, 'homographic replacement')
    
    @normalizers.normalize_delimiters
    def __call__(self, base_pkg: str, adversarial_pkg: str) -> int:
        normalized_base = base_pkg.replace('_', '')
        normalized_adversarial = adversarial_pkg.replace('_', '')
        is_homographic_replacement = homographic.generate_homographic_terminologies(normalized_base, normalized_adversarial)

        return 1 if is_homographic_replacement == True else 0

class OneStepLDDist(DetectorBase):
    key, name = (1, '1-step D-L dist')

    @normalizers.normalize_sequence_order(deep = False)
    @normalizers.normalize_delimiters
    def __call__(self, base_pkg: str, adversarial_pkg: str,
                    min_dist: int = 4, min_two_step_dist: int = 5) -> int:
        if len(base_pkg) < min_dist or len(adversarial_pkg) < min_dist: return 0
        if ''.join(base_pkg.split('-')) == ''.join(adversarial_pkg.split('-')): return 0
        for p in permutations(adversarial_pkg.split('_')): 
            
            dist = utils.DL_dist(base_pkg, '_'.join(p))
            if (len(base_pkg) < min_two_step_dist or len(adversarial_pkg) < min_two_step_dist) and dist == 2:
                return 0
            if dist in {1, 2}: return dist
        dist = utils.DL_dist(base_pkg, adversarial_pkg)
        if (len(base_pkg) < min_two_step_dist or len(adversarial_pkg) < min_two_step_dist) and dist == 2:
            return 0
        return dist if dist in {1, 2} else 0

class ScopeConfusion(DetectorBase):
    key, name = (11, 'scope confusion')
    is_scoped = True

    @normalizers.normalize_one_step_LD_dist
    @normalizers.normalize_delimiters
    def __call__(self, base_pkg: str, adversarial_pkg: str, *normalized_detectors) -> int:
        # if len(normalized_detectors) > 0 and '1-step-dl' in normalized_detectors[0].keys():
        #     print(f"{base_pkg}, {adversarial_pkg}: 1-step-dl + scope confusion")

        is_scope_confusion = False
        if  "/" in base_pkg or "/" in adversarial_pkg:
            normalized_base = base_pkg.split("/")
            normalized_adversarial = adversarial_pkg.split("/")
            
            # Case 1
            new_base = [string for string in normalized_base if not string.startswith("@")]
            new_ad = [string for string in normalized_adversarial if not string.startswith("@")]
            base_scope = [string for string in normalized_base if string.startswith("@")]
            adversarial_scope = [string for string in normalized_adversarial if string.startswith("@")]

            if new_base == new_ad:
                #pry()
                if len(base_scope) != 0:
                    base_scope  = base_scope[0].replace('@', "")
                if len(adversarial_scope) != 0:
                    adversarial_scope = adversarial_scope[0].replace("@", "")
                # Then check for typosquatting in the scopes

                if len(adversarial_scope) == 0 and len(base_scope) != 0:
                    is_scope_confusion = True 

                classifications = classify_typosquat(base_scope, adversarial_scope)
                if classifications:
                    is_scope_confusion = True

            # Case 2:
            normalized_base = base_pkg.replace("@", "").replace("/", "_").split("_")
            normalized_adversarial = adversarial_pkg.replace("@","").replace("/", "_").split("_")

            # Case 3: 
            # The package names are the same, then check if the scopes match other detectors.
            if "".join(normalized_base) == "".join(normalized_adversarial):
                is_scope_confusion = True

        return 1 if is_scope_confusion else 0


class SequenceReordering(DetectorBase):
    key, name = (7, 'sequence reordering')

    # @normalizers.normalize_one_step_LD_dist
    # @normalizers.normalize_grammar
    def __call__(self, base_pkg: str, adversarial_pkg: str) -> int:
        # implicitly normalizes delimiters
        base_sequence = utils.to_sequence(base_pkg)
        adversarial_sequence = utils.to_sequence(adversarial_pkg)
        if (base_sequence != adversarial_sequence) and (sorted(base_sequence) == sorted(adversarial_sequence)):
            return 1
        else:
            return 0


class DelimiterModification(DetectorBase):
    key, name = (3, 'delimiter modification')

    @normalizers.normalize_sequence_order
    @normalizers.normalize_one_step_LD_dist
    # @normalizers.normalize_grammar
    def __call__(self, base_pkg: str, adversarial_pkg: str, *normalized_detectors) -> int:
        # if len(normalized_detectors) > 0 and '1-step-dl' in normalized_detectors[0].keys():
        #     print(f"{base_pkg}, {adversarial_pkg}: 1-step-dl + delimiter modification")

        base_sequence = utils.to_sequence(base_pkg)
        base_seq_permutations = {''.join(element) for element in permutations(base_sequence)}
        adversarial_sequence = utils.to_sequence(adversarial_pkg)
        adversarial_seq_permuations = {''.join(element) for element in permutations(adversarial_sequence)}
        matched = (''.join(adversarial_sequence) in base_seq_permutations) or (''.join(base_sequence) in adversarial_seq_permuations)
        return 1 if matched and (base_pkg != adversarial_pkg) else 0


class PrefixSuffixAugmentation(DetectorBase):
    key, name = (4, 'prefix/ suffix augmentation')

    @normalizers.normalize_one_step_LD_dist
    @normalizers.normalize_delimiters
    # @normalizers.normalize_grammar
    def __call__(self, base_pkg: str, adversarial_pkg: str,  popularity_threshold: float = 0.15, *normalized_detectors) -> int:  # threshold 0.135 adds false negative, 0.145 is fine
        if len(base_pkg) < 3 or len(adversarial_pkg) < 3: return 0 # check for length of package name, 3

        # if len(normalized_detectors) > 0 and '1-step-dl' in normalized_detectors[0].keys():
        #     print(f"{base_pkg}, {adversarial_pkg}: 1-step-dl + prefix/suffix")

        normalized_base = base_pkg.replace('_', '')
        normalized_adversarial = adversarial_pkg.replace('_', '')

        if base_pkg in adversarial_pkg and (len(normalized_adversarial) > len(normalized_base)) and (len(normalized_adversarial) <= (len(normalized_base) * 2)):
            starts_with_or_ends_with = adversarial_pkg.startswith(base_pkg) or adversarial_pkg.endswith(base_pkg)

            if starts_with_or_ends_with and all((tokens.PKG_TOKEN_TO_RANK[seq] if seq in tokens.PKG_TOKEN_TO_RANK else 0) < popularity_threshold for seq in utils.to_sequence(base_pkg)):
                return 1
        return 0

class Simplification(DetectorBase):
    key, name = (6, 'simplification')   
    
    @normalizers.normalize_scope
    @normalizers.normalize_one_step_LD_dist
    @normalizers.normalize_delimiters
    def __call__(self, base_pkg: str, adversarial_pkg: str, *normalized_detectors) -> int:
        # if len(normalized_detectors) > 0 and '1-step-dl' in normalized_detectors[0].keys():
        #     print(f"{base_pkg}, {adversarial_pkg}: 1-step-dl + simplification")

        normalized_base = base_pkg.replace('_', '')
        normalized_adversarial = adversarial_pkg.replace('_', '')
        base_len = len(normalized_base)
        adv_len = len(normalized_adversarial)
        is_corner = normalized_base[:adv_len] == normalized_adversarial or normalized_base[base_len - adv_len:] == normalized_adversarial
        
        if is_corner and adversarial_pkg in base_pkg and (len(normalized_base) > len(normalized_adversarial)) and  (len(normalized_base) <= (len(normalized_adversarial)*2 + len(normalized_adversarial)/2)):
            return 1
        else:
            return 0


class GrammaticalSubstitution(DetectorBase):
    key, name = (10, 'grammatical substitution')

    @staticmethod
    def basic_plural_case(base_pkg: str, adversarial_pkg: str) -> bool:
        if len(base_pkg) == len(adversarial_pkg): return False
        lesser = min((base_pkg, adversarial_pkg), key = lambda s: len(s))
        greater = max((base_pkg, adversarial_pkg), key = lambda s: len(s))
        return (len(greater) == len(lesser) + 1 and greater[:-1] == lesser and greater[-1] == 's' and greater[-2] != 's') \
        or (len(greater) == len(lesser) + 1 and greater[:-1] == lesser and greater[-1] == 'r' and greater[-2] != 'r')

    @staticmethod
    def is_sub(base_token: str, adversarial_token: str) -> str:
        return base_token != adversarial_token and \
            ((nlp_tools.lemmatize(base_token) == nlp_tools.lemmatize(adversarial_token)) or \
                GrammaticalSubstitution.basic_plural_case(base_token, adversarial_token))

    @normalizers.normalize_sequence_order
    @normalizers.normalize_delimiters
    def __call__(self, base_pkg: str, adversarial_pkg: str) -> int:
        count = 0
        is_gramatical_substitution = False
        for base_token, adversarial_token in zip(base_pkg.split('_'), adversarial_pkg.split('_')):
            count  += int(GrammaticalSubstitution.is_sub(base_token, adversarial_token))

            if count > 0:
                base_segments = base_pkg.split('_')
                adversarial_segments = adversarial_pkg.split('_')
                base_segments.remove(base_token)
                adversarial_segments.remove(adversarial_token)

                if base_segments == adversarial_segments:
                    is_gramatical_substitution = True
        return is_gramatical_substitution

class SemanticSubstitution(DetectorBase):
    key, name = (8, "semantic substitution")
    
    # @normalizers.normalize_sequence_order
    @normalizers.normalize_one_step_LD_dist
    @normalizers.normalize_delimiters
    def __call__(self, base_pkg: str, adversarial_pkg: str, *normalized_detectors) -> int:
        if len(base_pkg) < 4 or len(adversarial_pkg) < 4: return 0 # check for length of package name, 4
        # if len(normalized_detectors) > 0 and '1-step-dl' in normalized_detectors[0].keys():
        #     print(f"{base_pkg}, {adversarial_pkg}: 1-step-dl + semantic substitution")

        base_tokens = utils.to_sequence(base_pkg)
        adversarial_tokens = utils.to_sequence(adversarial_pkg)
        if adversarial_tokens == adversarial_pkg:
            adversarial_tokens = utils.segment(adversarial_pkg)
        semantically_similar = semantic.is_semantically_similar(base_tokens, adversarial_tokens)
        return 1 if semantically_similar else 0

class HomophonicSimilarity(DetectorBase):
    key, name = (13, 'homophonic similarity')
    @staticmethod
    def is_similiar(base_token: str, adversarial_token: str) -> str:
        return base_token != adversarial_token and soundex(base_token) == soundex(adversarial_token) and metaphone(base_token) == metaphone(adversarial_token) and base_token in tokens.corpora['all']

    # @normalizers.normalize_sequence_order(deep = False)
    @normalizers.normalize_delimiters
    def __call__(self, base_pkg: str, adversarial_pkg: str) -> int:
        if len(base_pkg) < 4 or len(adversarial_pkg) < 4: return 0 # check for length of package name, 4

        caught = False
        for base_token, adv_token in zip(base_pkg.split('_'), adversarial_pkg.split('_')):
            p_adv_token = list(adv_token)
            for i in range(len(min(base_token, adv_token, key = len)) - 1):
                if base_token[i] + base_token[i + 1] == p_adv_token[i + 1] + p_adv_token[i] and base_token[i] != base_token[i + 1]:
                    p_adv_token[i], p_adv_token[i + 1] = p_adv_token[i + 1], p_adv_token[i]

            caught = HomophonicSimilarity.is_similiar(base_token, ''.join(p_adv_token))
            
            if caught:
                base_segments_test = base_pkg.split('_')
                adversarial_segments_test = adversarial_pkg.split('_')
                base_segments_test.remove(base_token)
                adversarial_segments_test.remove(adv_token)
                return base_segments_test == adversarial_segments_test

        return False

class AlternateSpelling(DetectorBase):
    key, name = (5, 'alternate spelling')

    @staticmethod
    def is_alternate(base_token: str, adv_token: str) -> str:
        base_translation = tokens.AM_TO_BR[base_token] if base_token in tokens.AM_TO_BR else None
        adv_translation = tokens.AM_TO_BR[adv_token] if adv_token in tokens.AM_TO_BR else None
        return base_translation == adv_token or adv_translation == base_token

    @normalizers.normalize_sequence_order
    @normalizers.normalize_delimiters
    def __call__(self, base_pkg: str, adversarial_pkg: str) -> int:
        for base_token, adv_token in zip(base_pkg.split('_'), adversarial_pkg.split('_')):
            count = sum([int(AlternateSpelling.is_alternate(base_token, adv_token))])
            if count >= 1:
                base_segments_test = base_pkg.split('_')
                adversarial_segments_test = adversarial_pkg.split('_')
                base_segments_test.remove(base_token)
                adversarial_segments_test.remove(adv_token)
                return count if (base_segments_test == adversarial_segments_test) else 0
        
        return count
