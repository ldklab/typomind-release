"""
Takes in raw *.csv file, drops uncategorized, standardizes/ labels instances, and writes clean data to new *.csv.
"""

import pandas as pd
import argparse
import sqlite3

from label_maps import raw_category_to_label


def make_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description = 'label and standardize raw *.csv')
    parser.add_argument('input_path', help = 'path to *.csv data')
    parser.add_argument('output_path', help = 'path to generate clean *.csv database, currently supports *.csv and *.sqlite')
    return parser


def main() -> None:
    parser = make_argparser()
    args = parser.parse_args()

    input_path: str = args.input_path
    output_path: str = args.output_path
    output_ext = output_path.rsplit('.')[-1]

    df = pd.read_csv(input_path)
    df.dropna(subset=['Categories'], inplace=True)
    df['Categories'] = df['Categories'].map({k: str(v) for k, v in raw_category_to_label.items()})
    df['Original Package Name'] = df['Original Package Name'].map(lambda name: name.strip() if isinstance(name, str) else '')
    df['Malicious Package Name'] = df['Malicious Package Name'].map(lambda name: name.strip() if isinstance(name, str) else '')

    if output_ext == 'csv':
        df.to_csv(output_path, index = False)
    elif output_ext == 'sqlite':
        with sqlite3.connect(output_path) as con:
            df.to_sql('packages', con, index = False, if_exists = 'replace')


if __name__ == '__main__':
    main()