"""Project main script"""
from pathlib import Path

from fcn.processing import process_file

if __name__ == '__main__':
    process_file(Path("data/test/vety_HDS.ortho.txt"))
