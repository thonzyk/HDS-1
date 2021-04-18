import os
from unitselection.fcn.constants import *
import pickle as plk
from scipy.io import wavfile
import matplotlib
from matplotlib import pyplot as plt
from unitselection.fcn.inventory_diphone import load_inventory, load_phonemes_sim
import random
from unitselection.fcn.viterbi import *

matplotlib.use('Qt5Agg')


def concat_phones(phones):
    phon_lens = [len(element) for element in phones]
    total_len = sum(phon_lens)

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


def get_best_sequence(sentence, inv, phonemes_sim):
    return get_optimal_signal(sentence, inv, phonemes_sim)


def testing():
    inv = load_inventory(DATA_DIR / PREP)
    phonemes_sim = load_phonemes_sim(DATA_DIR / PREP)

    # txt = "|$|sakra|#|Wimi|#|tohle|je|kAva|!opravdovejG|znalcU|nAm|bi|s|vincentem|bejvalo|staCilo|!obiCejnI|granulovanI|kafe|!a|!on|na|nAs|vitAhne|tuhle|gurmAnsky|specialitu|$|"
    txt = "koNomPd"

    txt = txt.replace('|', '')
    txt = txt.replace('#', '')

    diphones = to_diphones(txt)

    sequence = get_best_sequence(diphones, inv, phonemes_sim)
    sound = concat_phones(sequence)
    wavfile.write(DATA_DIR / OUT / "TEST.wav", SAMPLE_RATE, sound)


if __name__ == '__main__':
    inv = load_inventory(DATA_DIR / PREP)
    phonemes_sim = load_phonemes_sim(DATA_DIR / PREP)

    with open("C:/Users/tomas/Documents/FAV/HDS/semestralky/1/reseni/HDS-1/phonetrans/data/output/vety_HDS.phntrn.txt",
              'r') as fr:
        lines = fr.read().splitlines()
        for i, line in enumerate(lines):
            line = line.replace('|', '')
            line = line.replace('#', '')
            diphones = to_diphones(line)

            sequence = get_best_sequence(diphones, inv, phonemes_sim)
            sound = concat_phones(sequence)
            f_name = str(i).zfill(4) + ".wav"
            wavfile.write(DATA_DIR / OUT / f_name, SAMPLE_RATE, sound)
