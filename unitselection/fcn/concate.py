import os
from unitselection.fcn.constants import *
import pickle as plk
from scipy.io import wavfile
import matplotlib
from matplotlib import pyplot as plt
from unitselection.fcn.inventory_phoneme import load_inventory
import random

matplotlib.use('Qt5Agg')


def concat_phones(phones):
    phon_lens = [len(element) for element in phones]
    total_len = sum(phon_lens)
    # total_len -= int((MIN_LENGTH * (len(phones) - 1)) // 2)

    sound = np.zeros((total_len,))

    prev_sound_i = 0
    sound_i = prev_sound_i

    for phone in phones:
        sound_i += len(phone)
        sound[prev_sound_i:sound_i] += phone
        # sound_i -= FADE_LEN
        prev_sound_i = sound_i

    return sound.astype('int16')


if __name__ == '__main__':
    inv = load_inventory()

    txt = "|$|sykromI|lEkaRi|si|tak|sTeZujI|na|situaci|#|gdi|jim|rosty|pQedefSIm|nAkladi|na|!energiji|!a|zAroveJ|jim|stAt|reguluje|ceni|$|"
    txt = txt.replace('|', '')

    phones = []

    for chr in txt:
        variants = inv[chr]
        variant = random.randint(0, len(variants) - 1)
        variant = variants[variant]
        phones.append(variant)

    sound = concat_phones(phones)

    wavfile.write(DATA_DIR / OUT / "TEST.wav", SAMPLE_RATE, sound)
