import numpy as np
import pandas as pd
from unitselection.fcn.constants import *
from scipy.io import wavfile
import matplotlib
from matplotlib import pyplot as plt
from unitselection.fcn.inventory_phoneme import load_inventory

matplotlib.use('Qt5Agg')


def is_data_line(line):
    return line[0].isnumeric()


def is_new_sentence_line(line):
    return line.startswith("\"*/Sentence")


def split_mlf():
    with open(DATA_DIR / ORIG_MLF, 'r', encoding='utf-8') as fr:

        fw = open(DATA_DIR / MLF / "Sentence00001.mlf", 'w', encoding='utf-8')

        for line in fr:
            if is_new_sentence_line(line):
                fw.close()
                f_name = line[3:16] + ".mlf"
                fw = open(DATA_DIR / MLF / f_name, 'w', encoding='utf-8')
            elif is_data_line(line):
                fw.write(line)

        fw.close()


def check_wav():
    sample_rate, data = wavfile.read(DATA_DIR / SPC / "Sentence00001.wav")

    ts = 1.0 / sample_rate

    t = np.linspace(0, ts * len(data), len(data))

    # plt.plot(t, data)
    # plt.show()

    wavfile.write(DATA_DIR / OUT / "SENTENCE00001.wav", sample_rate, data)

    print()


def get_phones_lengths():
    pass


def analyse_phones_lengths():
    inv = load_inventory()

    keys = [key for key in inv]

    lengths = []

    corrupted_chars = []

    for key in inv:
        lst = inv[key]
        for signal in lst:
            length = len(signal) * 6.25e-05
            # if length < 1.0:
            lengths.append(length)

            if 0.25 < length < 0.5:
                corrupted_chars.append(key)

    corrupted_chars = list(set(corrupted_chars))

    print("max: " + str(max(lengths)))
    print("min: " + str(min(lengths)))

    plt.hist(lengths, 1000)
    plt.show()


if __name__ == '__main__':
    analyse_phones_lengths()
