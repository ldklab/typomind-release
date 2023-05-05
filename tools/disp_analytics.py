"""
Display analytics labeled dataset
"""

import pandas as pd
import argparse
import sqlite3
from functools import reduce

from label_maps import label_to_std_category


def make_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description = 'display package analytics')
    parser.add_argument('input_path', help = 'path to clean data file, currently supports *.csv and *.sqlite')
    parser.add_argument('output_path', nargs='?', default = None, help = 'path to output analytics to, must be *.csv')
    return parser


def main() -> None:
    parser = make_argparser()
    args = parser.parse_args()

    input_path: str = args.input_path
    output_path: str = args.output_path
    if not output_path is None and not output_path.endswith('.csv'):
        output_path += '.csv'
    input_ext = input_path.rsplit('.')[-1]

    if input_ext == 'csv':
        df = pd.read_csv(input_path)
    elif input_ext == 'sqlite':
        with sqlite3.connect(input_path) as con:
            df = pd.read_sql_query('SELECT * FROM packages', con)
    else:
        raise TypeError(f'"{input_path}" is not a valid input path')

    categories: pd.Series = df.Categories
    for i, instance in enumerate(categories):  # converting numerical labels to str descriptions
        categories[i] = ' || '.join({label_to_std_category[k] for k in eval(instance)})

    formatted_df = pd.merge(  # constructing counts and percentages
        categories.value_counts().rename_axis('CATEGORY').reset_index(name='COUNT'),
        (categories.value_counts(normalize=True).mul(100).round(1).astype(str) + '%').rename_axis('CATEGORY').reset_index(name='FREQ'),
        how='inner',
        on='CATEGORY'
    )

    formatted_df.loc[''] = [  # adding totals as footer
        'TOTAL',
        formatted_df.COUNT.sum(),
        str(round(reduce(lambda base, other: base + float(other[:-1]), formatted_df.FREQ, 0))) + '%'
    ]

    if output_path: formatted_df.to_csv(output_path, index_label='CATEGORY', index = False)
    else: print(formatted_df)


if __name__ == '__main__':
    main()