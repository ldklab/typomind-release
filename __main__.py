"""

"""

import os.path as osp, os
import argparse
from itertools import product
from icecream import ic
import logging
from datetime import datetime
import pry
from core.detectors import classify_typosquat


def make_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description = 'displays typo-squatting categories exhibited by adversarial package WRT base package')
    parser.add_argument('base_package', help='name of original package')
    parser.add_argument('adv_package', help='name of potentially malicious package')
    parser.add_argument('--base_file', '-bf', action='store_const', const=True, help='specify that base names is path to list of pkgs')
    parser.add_argument('--adv_file', '-af', action='store_const', const=True, help='specify that adv names is path to list of pkgs')
    parser.add_argument('--outfile_path', '-of', help='specify that file is path to output')
    return parser


def main():
    argparser = make_argparser()
    args = argparser.parse_args()
    base_pkg_spec: str = args.base_package
    adv_pkg_spec: str = args.adv_package
    base_file: bool = args.base_file
    adv_file: bool = args.adv_file
    outfile_path: str = args.outfile_path

    logging.basicConfig(filename="logs/run.log", filemode='a', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    logging.info("Typomind Detector Starting ....")

    # outfile_path = "output/detector-output-multithreading.txt"

    if base_file:
        assert osp.isfile(base_pkg_spec)
        with open(base_pkg_spec, 'r') as f:
            base_pkgs = {pkg.strip() for pkg in f}
    else: base_pkgs = {base_pkg_spec}
    if adv_file:
        assert osp.isfile(adv_pkg_spec)
        with open(adv_pkg_spec, 'r') as f:
            adv_pkgs = {pkg.strip() for pkg in f}
    else: adv_pkgs = {adv_pkg_spec}
    count = 0
    
    for base_pkg, adv_pkg in product(base_pkgs, adv_pkgs):
        start_time = datetime.now()
        try:
            classifications = {name: c for (_, name), c in classify_typosquat(base_pkg, adv_pkg).items()}
            if classifications:
                if outfile_path:
                    with open(outfile_path, 'a') as file:
                        end_time = datetime.now()
                        file.write(f'(\'{base_pkg}\', \'{adv_pkg}\'): {classifications}, {format(end_time - start_time)}')
                        file.write('\n')
                end_time = datetime.now()
                print(f'(\'{base_pkg}\', \'{adv_pkg}\'): {classifications}, {format(end_time - start_time)}')
        except Exception as e:
            end_time = datetime.now()
            logging.error(f"Unhandled exception for base: {base_pkg}  and adv: {adv_pkg}. {format(end_time - start_time)}, Error{e}, ")
            continue
        count += 1

        if count % 100000 == 0:
            logging.info(f"Packages checked: {count}")

    print("Total product: ", count)


if __name__ == '__main__':
    main()