from scipy.io import wavfile
import pickle as plk
from unitselection.fcn.constants import *
import os
import random


def load_inventory(dir):
    with open(dir / "inventory.plk", 'rb') as fr:
        inv = plk.load(fr)
    return inv


def create_directories():
    inv = load_inventory(DATA_DIR / PREP)
    i = 1
    for key in inv:
        key = key + "_____" + str(i)
        os.mkdir(DATA_DIR / OUT / "signals" / key)
        i += 1


if __name__ == '__main__':
    # create_directories()

    inv = load_inventory(DATA_DIR / PREP)
    i = 1
    for key in inv:
        units_list = inv[key]
        key = key + "_____" + str(i)
        for j, unit in enumerate(units_list):
            wavfile.write(DATA_DIR / OUT / "signals" / key / str(str(j) + ".wav"), SAMPLE_RATE, unit.signal.astype('int16'))

        i += 1

    print()
