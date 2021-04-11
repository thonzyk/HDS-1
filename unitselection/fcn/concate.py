import os
from unitselection.fcn.constants import *
import pickle as plk
from scipy.io import wavfile
import matplotlib
from matplotlib import pyplot as plt
from unitselection.fcn.inventory_diphone import load_inventory
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
        sound_i -= FADE_LEN
        prev_sound_i = sound_i

    return sound.astype('int16')


def to_diphones(sentence):
    new_sentence = []

    last_phoneme = sentence[0]

    for phoneme in sentence[1:]:
        diphone = last_phoneme + phoneme
        last_phoneme = phoneme
        new_sentence.append(diphone)

    return new_sentence


def get_best_sequence(sentence, inv):
    sequence = []
    for diphone in sentence:
        if diphone not in inv:
            print("missing diphone")
            continue

        variants = inv[diphone]
        variant = random.randint(0, len(variants) - 1)
        variant = variants[variant]
        sequence.append(variant.signal)

    return sequence


if __name__ == '__main__':
    inv = load_inventory()

    txt = "$TImpQecetkiJesenAtu!okresJIhosyduf!uherskEmhraDiSTiradomIraveselA!odUvoDJila#!osvobozeJIdevjetasedmdesATiletEhovlaDimIrazavaDilIka$"
    txt = txt.replace('|', '')

    diphones = to_diphones(txt)

    sequence = get_best_sequence(diphones, inv)

    # phones = []
    #
    # last_chr = '$'
    #
    # for chr in txt:
    #     diphone = last_chr + chr
    #     if diphone not in inv:
    #         last_chr = chr
    #         print("missing diphone")
    #         continue
    #     variants = inv[diphone]
    #     last_chr = chr
    #     variant = random.randint(0, len(variants) - 1)
    #     variant = variants[variant]
    #     phones.append(variant.signal)

    sound = concat_phones(sequence)

    wavfile.write(DATA_DIR / OUT / "TEST.wav", SAMPLE_RATE, sound)
