"""
DESCRIPTION: Evaluates detectors on full dataset, prints statistics, and optionally writes results to *.csv file.

NOTES:
- could artificially generate examples to augment dataset
"""

import sys
sys.path.append('.')
import sqlite3
import pandas as pd
import argparse
from pipe import traverse
from tqdm import trange
from collections import defaultdict
from icecream import ic
import json

from core.detectors import classify_typosquat, DetectorBase
from tools.label_maps import label_to_std_category


OMIITED = {12}


def make_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description = 'display package analytics')
    parser.add_argument('input_path', help = 'path to clean data file, currently supports *.csv or *.sqlite')
    parser.add_argument('output_path', nargs='?', default = None, help = '*.csv path to generate result table to')
    parser.add_argument('--verbose', '-v', action='store_const', const=True, help='print detailed results')
    return parser


def main():
    # get and process command line arguments
    parser = make_argparser()
    args = parser.parse_args()

    input_path: str = args.input_path
    output_path: str = args.output_path
    input_ext = input_path.rsplit('.')[-1]
    verbose: bool = args.verbose

    # load input data into data frame
    if input_ext == 'csv':
        df = pd.read_csv(input_path, keep_default_na=False)
    elif input_ext == 'sqlite':
        with sqlite3.connect(input_path) as con:
            df = pd.read_sql_query('SELECT * FROM packages', con)
            df.fillna('')
    else:
        raise TypeError(f'"{input_path}" is not a valid input path')

    # now lets pass each case to detectors and see how accurate they are
    detected = []
    not_detected = []
    passed = []
    failed = []
    crashed = []
    result_log = []

    n = len(df.index)
    for i in trange(n):
        adversarial_pkg, base_pkg, ecosystem, str_labels, note, src = df.loc[i]
        true_labels = tuple(sorted(eval(str_labels)))
        if any(l in OMIITED for l in true_labels) or ' ' in base_pkg:
            n -= 1
            continue
        try:
            if len(base_pkg) > 100 or len(adversarial_pkg) > 100:
                raise ValueError('Exceeds 100 chars.')
            results = classify_typosquat(base_pkg.lower(), adversarial_pkg.lower())
        except Exception as e:  # at least one of the detectors couldn't handle the case
            #raise e  # NOTE uncomment this to see error
            crashed.append((base_pkg, adversarial_pkg))
            if not (e.args and e.args[0] == 'Exceeds 25 chars.'):
                not_detected.append((base_pkg, adversarial_pkg, (), true_labels))
            result_log.append((base_pkg, adversarial_pkg, ecosystem, note, src, str(true_labels), 'None', 'crashed'))
            continue
        actual_labels = tuple(sorted([count * [key] for (key, _), count in results.items()] | traverse))
        if bool(actual_labels) == bool(true_labels): detected.append((base_pkg, adversarial_pkg, true_labels))
        else: not_detected.append((base_pkg, adversarial_pkg, actual_labels, true_labels))

        if true_labels == actual_labels:
            passed.append((base_pkg, adversarial_pkg, actual_labels))
            outcome = 'passed'
        else:
            failed.append((base_pkg, adversarial_pkg, actual_labels, true_labels))
            outcome = 'failed'
        result_log.append((base_pkg, adversarial_pkg, ecosystem, note, src, str(true_labels), str(actual_labels), outcome))
    print()

    # lets take a look at the results
    # first, the failed cases
    false_positives = set()
    false_negatives = set()
    # we'll evaluate each detector individually too
    detector_accuracy = defaultdict(lambda: {'correct': 0, 'false_positive': 0, 'false_negative': 0})
    total_labels = 0
    if failed:  # if any failed
        if verbose: print(f'Detectors failed on {len(failed)} cases:')
        for case in failed:
            base_pkg, adversarial_pkg, actual_labels, true_labels = case
            if verbose: print(f'\t[\'{base_pkg}\' > \'{adversarial_pkg}\']: got {actual_labels}, expected {true_labels}')
            actual_label_to_count = {label: actual_labels.count(label) for label in set(label_to_std_category)}  # count how many times each detector was triggered
            true_label_to_count = {label: true_labels.count(label) for label in set(label_to_std_category)}  # count how many times each detector SHOULD be triggered
            
            case_true_positives = {label: min(actual_label_to_count[label], true_label_to_count[label]) for label in set(label_to_std_category)}  # count how many times the detector was triggered correctly
            for label, count in case_true_positives.items(): detector_accuracy[label]['correct'] += count

            # false positives are those cases where a detector got triggered more times than it should have
            case_false_positives = {label: count - true_label_to_count[label] for label, count in actual_label_to_count.items() if count > true_label_to_count[label]}
            
            # false negatives are those cases where a detector SHOULD have gotten triggered more times than it actually did
            case_false_negatives = {label: count - actual_label_to_count[label] for label, count in true_label_to_count.items() if count > actual_label_to_count[label]}
            if case_false_positives:
                false_positives.add(case)
                for label, count in case_false_positives.items():
                    detector_accuracy[label]['false_positive'] += count
            if case_false_negatives:
                false_negatives.add(case)
                for label, count in case_false_negatives.items():
                    detector_accuracy[label]['false_negative'] += count
            total_labels += len(true_labels)

        if verbose and false_positives:
            print()
            print(f'Identified {len(false_positives)} false positives:')
            for base_pkg, adversarial_pkg, actual_labels, true_labels in false_positives:
                print(f'\t[\'{base_pkg}\' > \'{adversarial_pkg}\']: got {actual_labels}, expected {true_labels}')

        if verbose and false_negatives:
            print()
            print(f'Identified {len(false_negatives)} false negatives:')
            for base_pkg, adversarial_pkg, actual_labels, true_labels in false_negatives:
                print(f'\t[\'{base_pkg}\' > \'{adversarial_pkg}\']: got {actual_labels}, expected {true_labels}')
        if verbose: print()

    # not as useful to look at, just need to add up some labels for analysis
    if passed:
        for base_pkg, adversarial_pkg, actual_labels in passed:
            for label in actual_labels:
                detector_accuracy[label]['correct'] += 1
            total_labels += len(actual_labels)

    if verbose and not_detected:
        print(f'Failed to detect {len(not_detected)} cases:')
        for base_pkg, adversarial_pkg, actual_labels, true_labels in not_detected:
            print(f'\t[\'{base_pkg}\' > \'{adversarial_pkg}\']: got {actual_labels}, expected {true_labels}')
        print()

    if verbose and crashed:
        print(f'Detectors crashed on {len(crashed)} cases:')
        for base_pkg, adversarial_pkg in crashed:
            print(f'\t[\'{base_pkg}\' > \'{adversarial_pkg}\']')
        print()

    # lets see what we discovered...
    print('SUMMARY:')
    # general
    print(f'Passed {len(passed)}/{n} ({round(100 * len(passed) / n, 2)}%) cases')
    print(f'Failed {len(failed)}/{n} ({round(100 * len(failed) / n, 2)}%) cases')
    print(f'Crashed {len(crashed)}/{n} ({round(100 * len(crashed) / n, 2)}%) cases')
    print(f'Detected {len(detected)}/{n} ({round(100 * len(detected) / n, 2)}%) cases')

    # false positives and negatives
    print()
    print(f'{len(false_positives)} failed cases contained false positives ({round(100 * len(false_positives) / len(failed), 2)}%)')
    print(f'{len(false_negatives)} failed cases contained false negatives ({round(100 * len(false_negatives) / len(failed), 2)}%)')
    print(f'{len(false_negatives & false_positives)} failed cases contained both false positives and false negatives ({round(100 * len(false_negatives & false_positives) / len(failed), 2)}%)')
    
    # detectors
    print()
    enabled_detectors = set(d_id for d_id, d in DetectorBase.cls_registry.items() if d.enabled)
    print(f'Ran tests on {len(enabled_detectors)}/{len(label_to_std_category)} detectors')
    
    print()
    print('Detector accuracy:')
    detector_results = {}
    for label, stats in sorted(detector_accuracy.items(), key = lambda item: item[0]):
        if label in enabled_detectors:
            tp, fp, fn = stats['correct'], stats['false_positive'], stats['false_negative']
            tn = total_labels - tp - fp - fn
            try:
                precision = tp / (tp + fp)
                recall = tp / (tp + fn)
                accuracy = (tp + tn) / total_labels
                f1_score = 2 * ((precision * recall) / (precision + recall))
            except ZeroDivisionError:
                precision = float('nan')
                recall = float('nan')
                accuracy = float('nan')
                f1_score = float('nan')
            detector_results[f'{label}: {label_to_std_category[label]}'] = {
                'tp': tp,
                'tn': tn,
                'fp': fp,
                'fn': fn,
                'precision': precision,
                'recall': recall,
                # 'accuracy': accuracy,
                'f1_score': f1_score,
            }
            print(f'\tDetector {label} (\'{label_to_std_category[label]}\'):')
            print(f'\t\t(TP, TN, FP, FN) = ({tp}, {tn}, {fp}, {fn})')
            print(f'\t\tPrecision: {round(precision, 5)}')
            print(f'\t\tRecall: {round(recall, 5)}')
            print(f'\t\tAccuracy: {round(accuracy, 5)}')
            print(f'\t\tF1 Score: {round(f1_score, 5)}')
            print()

    # write results to file
    result_table = pd.DataFrame(
        result_log,
        columns = ['base_pkg', 'adversarial_pkg', 'ecosystem', 'notes', 'source', 'detected_categories', 'actual_categories', 'outcome']
    )
    
    if output_path:
        result_table.to_csv(output_path + '.csv', index = False)
        with open(output_path + '.json', 'w') as f:
            json.dump(detector_results, f, indent=2)


if __name__ == '__main__':
    main()