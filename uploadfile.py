#!/usr/bin/env python3
"""
Requires Python 3.4
"""
# from drive_api import Drive
from gg.oauth2 import create_creds_folder
from gg.drive import Drive
import os
import argparse


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument(dest="file")
    # parser.add_argument('-s', '--chunksize',dest="chunksize", default=4096, type=int)
    parser.add_argument('-v', '--verbose', dest="verbose", default=False, nargs='?')
    return parser.parse_args()


def run(a):
    assert a.file.lstrip()[0:2] != '..', 'parent folder is prohibited'
    assert a.file.lstrip()[0] != '/', 'root folder is prohibited'
    assert a.file.find('"') == -1, 'double quote is prohibited'
    isdir = os.path.isdir(a.file)
    assert not isdir, '%s is a directory' % a.file

    try:
        create_creds_folder()
        Drive().upload(a.file)
    except Exception as e:
        print(e)
        if a.verbose is None:
            raise


if __name__ == '__main__':
    a = args()
    try:
        run(a)
    except Exception as e:
        print(e)
        if a.verbose is None:
            raise
