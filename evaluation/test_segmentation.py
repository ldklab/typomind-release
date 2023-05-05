"""
Tests delimiter-less segmentation
"""

import sys; sys.path.append('.')
from icecream import ic
from tqdm import tqdm

print('Loading segmenter...')
from core.utils import segment
print('Segmenter loaded.')

positives = {
    'coinstring': ['coin', 'string'],
    'coinpayment': ['coin', 'payment'],
    'bs85check': ['bs85', 'check'],
    'bs85': ['bs85'],
    'bitcoinjs': ['bitcoin', 'js'],
    'bufferxor': ['buffer', 'xor'],
    'activesupport': ['active', 'support'],
    'simplejson': ['simple', 'json'],
    'easyinstall': ['easy', 'install'],
    'pwdhash': ['pwd', 'hash'],
    'bz2file': ['bz2', 'file'],
    'urllib3': ['url', 'lib', '3'],
    'mitmproxy': ['mitm', 'proxy'],
    'pyftpdlib': ['py', 'ft', 'pd', 'lib'],
    'pysqlite': ['py', 'sqlite'],
    'pymongodb': ['py', 'mongo', 'db'],
    'pyyaml': ['py', 'yaml'],
    'pyspark': ['py', 'spark'],
    'html5lib': ['html5', 'lib'],
    'pycurl': ['py', 'curl'],
    'abilityengine': ['ability', 'engine'],
    'abstractimporter': ['abstract', 'importer'],
    'actionparameter': ['action', 'parameter'],
    'activeprofiling': ['active', 'profiling'],
    'activemodel': ['active', 'model'],
    'activerecord': ['active', 'record'],
    'elasticsearch': ['elastic', 'search'],
    'airbrake': ['air', 'brake'],
    'batchapi': ['batch', 'api'],
    'applicationconfig': ['application', 'config'],
    'arlightning': ['ar', 'lightning'],
    'asciidoctor': ['ascii', 'doctor'],
    'assemblyclient': ['assembly', 'client'],
    'authclick': ['auth', 'click'],
    'authvalidate': ['auth', 'validate'],
    'awsupload': ['aws', 'upload'],
    'batchinsert': ['batch', 'insert'],
    'catdog': ['cat', 'dog'],
    'datadogapm': ['data', 'dog', 'apm'],
    'fontleague': ['font', 'league'],
    'movingaverage': ['moving', 'average'],
    'playingcards': ['playing', 'cards'],
    'seleniumspider': ['selenium', 'spider'],
    'applogger': ['app', 'logger'],
    'discordsafety': ['discord', 'safety'],
    'vuecoinpaymentsjs': ['vue', 'coin', 'payments', 'js'],
    'spidermonkey': ['spider', 'monkey'],
    'twittercards': ['twitter', 'cards'],
    'livingdead': ['living', 'dead'],
    'hackcards': ['hack', 'cards'],
}

negatives = {
    'js',
    'commander',
    'buffer',
    'colorama',
    'colourama',
    'mongo',
    'parse',
    'sparkles',
    'regenerator',
    'socket',
    'request',
    'sha',
    'notification',
    'loader',
    'transport',
    'service',
    'numpy',
    'matplotlib',
    'python',
    'function',
    'acceptance',
    'enumerable',
    'subscriber',
    'publishable',
    'administrate',
    'alphabet',
    'documentation',
    'database',
    'assembly',
    'developer',
    'translations',
    'plugins',
    'formatter',
    'github',
    'language',
    'spider',
    'telegram',
    'fortnite',
    'yandex',
    'selenium',
    'playing',
    'team',
    'assets',
    'common',
    'handler',
    'batched',
    'localize',
    'deploy',
    'normalizer',
    'validations'
}

all_data = positives | {k: [k] for k in negatives}

def main():
    segmented_negative = set()  # should NOT be segmented but got segmented
    unsegmented_negative = set()  # should NOT be segmented and was NOT segmented
    unsegmented_positve = set()  # should be segmented but was NOT segmented
    segmented_positve_correct = set()  # should be segmented and was segmented correctly
    segmented_positve_incorrect = set()  # should be segmented and was segmented but incorrectly

    correct = set()
    incorrect = set()

    actual_segmentations = {}
    
    for raw, true_segmentation in tqdm(all_data.items(), desc = 'Testing segmenter'):
        actual_segmentation = segment(raw)
        actual_segmentations[raw] = actual_segmentation
        
        true_segmented = len(true_segmentation) > 1  # true ouput is segmented
        actual_segmented = len(actual_segmentation) > 1  # actual output is segmented
        is_correct = true_segmentation == actual_segmentation

        if is_correct:  # segmented correctly
            correct.add(raw)
            if true_segmented:  # correct and included segmentation
                segmented_positve_correct.add(raw)
            else:  # correct and did not segment
                unsegmented_negative.add(raw)
        else:  # segmented inccorectly
            incorrect.add(raw)
            if true_segmented:  # should have been segmented
                if actual_segmented:  # incorrect, although did segment where shld have, did so incorrectly
                    segmented_positve_incorrect.add(raw)
                else:  # incorrect becuase should have been segmented but was not
                    unsegmented_positve.add(raw)
            else:  # incorrect because should not have segmented, but did segment
                segmented_negative.add(raw)

    print('INCORRECT')
    for raw in incorrect:
        print(f'"{raw}":')
        print(f'\tactual: {actual_segmentations[raw]}')
        print(f'\ttrue: {all_data[raw]}')
    print()

    print('CORRECT')
    for raw in correct:
        print(f'"{raw}": {all_data[raw]}')
    print()

    ic(len(positives))
    ic(len(negatives))
    print()
    ic(len(segmented_negative))
    ic(len(unsegmented_negative))
    ic(len(unsegmented_positve))
    ic(len(segmented_positve_correct))
    ic(len(segmented_positve_incorrect))
    print()
    ic(len(correct))
    ic(len(incorrect))





if __name__ == '__main__':
    main()
