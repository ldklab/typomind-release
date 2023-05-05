

from gensim.models import  KeyedVectors

from core import utils
from core import tokens
import pry

WORD_VECTOR = KeyedVectors.load('core/models/fasttext-vectors.kv')

def get_similarity(first_word, second_word):
	try:
		similarity = WORD_VECTOR.similarity(first_word, second_word)
	except KeyError:
		similarity = 0
	return similarity

def is_semantically_similar(base_token, adverserial_token):
    bt, at = [b for b in base_token if b not in adverserial_token], [a for a in adverserial_token if a not in base_token]

    permutations = [(x,y) for x in bt for y in at]
    
    if len(permutations) == 0:
        return False

    total_similarity = 0
    for combination in permutations:
        total_similarity += get_similarity(combination[0], combination[1])
    
    similarity_ratio = total_similarity / len(permutations)

    # print(f"{str(base_token)} and {str(adverserial_token)} have similarity ratio of {similarity_ratio}")
    if similarity_ratio < 0.65:
        return False
    
    return True

def check_asemantic(base_token, adversarial_token, popularity_threshold: float = 0.02502):  # recall first drops below 0.02502, threshold seems to be very sensitive
    base_normalized = utils.to_sequence(base_token)
    adversarial_normalized = utils.to_sequence(adversarial_token)

    base_len = len(base_normalized)
    adverserial_len = len(adversarial_normalized)
    is_asemantic = False

    if base_len > 1 and adverserial_len > 1:
        bt, at = [b for b in base_normalized if b not in adversarial_normalized], [a for a in adversarial_normalized if a not in base_normalized]
        sbt, sat = [b for b in base_normalized if b in adversarial_normalized], [a for a in adversarial_normalized if a in base_normalized]

        # Check only for conditions where there is 1 token substitution
        if len(sbt) == 1 and len(sat) == 1 and len(at) ==1 and len(bt) ==1:
            is_of_appropriate_length = len(''.join(sat)) < (len(''.join(sbt)) * 2)
            if len(bt) !=0 and bt != base_normalized and len(at) != 0 and at !=adversarial_normalized and len(bt) == len(at) and is_of_appropriate_length:
                base_in_tokens  = all([term in tokens.corpora['tech'] for term in bt])
                adverse_in_tokens = all([term in tokens.corpora['tech'] for term in at])

                if base_in_tokens and adverse_in_tokens:
                    semantically_similar = is_semantically_similar(bt, at)
                    if not semantically_similar:
                        # lets check, perhaps the rest of the tokens are just super common and popular?
                        if all((tokens.PKG_TOKEN_TO_RANK[seq] if seq in tokens.PKG_TOKEN_TO_RANK else 0) < popularity_threshold for seq in sbt):
                            is_asemantic = True 
    
    return is_asemantic
	










	
