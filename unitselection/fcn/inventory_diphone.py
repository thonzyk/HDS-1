import bisect
import os
import pickle as plk

import matplotlib
from scipy.io import wavfile
from matplotlib import pyplot as plt

from unitselection.fcn.speech_unit import SpeechUnit

from phonetrans.fcn.constants import UNVOICED_CONSONANTS, VOICED___CONSONANTS, VOWELS
import random

from unitselection.fcn.constants import *

matplotlib.use('Qt5Agg')


def get_pitch_marks(pm_f_name):
    """
    :param pm_f_name: source file containing the pitch mark information
    :return: list of tuples, where first element is time and second type of the pitch mark represented by a letter
    """
    pms = []
    with open(pm_dir / pm_f_name, 'r', encoding='utf-8') as pm_f:
        for line in pm_f:
            if line[0] == ' ':
                line = line[1:]
            line = line[:-1]
            items = line.split(' ')

            typ = items[-1]
            if typ == 'T':
                continue

            time = float(items[0])

            pms.append((time, typ))

    return pms


def get_closest_pitch_mark():
    pass


def get_index_in_signal(signal, moment, sample_rate):
    """

    :param signal: 1D ndarray representing the signal amplitude time series
    :param moment: wanted time moment in seconds
    :param sample_rate: signal sample rate
    :return: closest index corresponding with the desired moment
    """


def get_signal_cut(signal, start, stop):
    """
    :param signal: 1D ndarray representing the signal amplitude time series
    :param sample_time: signal sample time [second]
    :param start: start of the cut time [seconds]
    :param stop: start of the cut time [seconds]
    :return: subsignal cut out of the original signal based on the given time window corrected by the pitch marks.
    """

    start_i = round(start / SAMPLE_TIME)
    stop_i = round(stop / SAMPLE_TIME)

    return signal[start_i:stop_i]


def nearest_pitchmark(pms, time):
    pm_time_i = bisect.bisect_right(pms, (time,))
    time_pm = pms[pm_time_i][0]

    return time_pm


def add_fade(signal):
    """
    :param signal: 1D ndarray representing the signal amplitude time series
    :param signal: window used to perform fade
    :return: signal with fade-in and fade-out regions
    """

    win_half = len(WINDOW) // 2

    signal[:win_half] *= WINDOW[:win_half]
    signal[-win_half:] *= WINDOW[-win_half:]

    return signal


def get_phonem(line):
    line = line[:-1]
    items = line.split(' ')
    start = float(items[0]) * TIME_STEP
    stop = float(items[1]) * TIME_STEP
    center = (start + stop) / 2

    phoneme = items[2]

    return phoneme, start, stop, center


def get_sentence(mlf_f_name, pms):
    sentence = []

    with open(mlf_f_name, 'r', encoding='utf-8') as mlf_f:

        first_line = True

        for line in mlf_f:
            if first_line:
                last_phoneme = '$'
                last_center = 0.0
                first_line = False
                continue

            phoneme, start, stop, center = get_phonem(line)

            center = nearest_pitchmark(pms, center)

            sentence.append((last_phoneme + phoneme, last_center, center))
            last_center = center
            last_phoneme = phoneme

    return sentence


def create_inventory(mlf_dir, pm_dir, spc_dir, inv_f_name):
    _, _, mlf_files = next(os.walk(mlf_dir))

    inv = dict()

    for mlf_f_name in mlf_files:
        pm_name = mlf_f_name[:-4] + ".pm"
        spc_name = mlf_f_name[:-4] + ".wav"

        sample_rate, signal = wavfile.read(DATA_DIR / SPC / spc_name)

        signal = signal.astype('float32')
        pms = get_pitch_marks(pm_dir / pm_name)

        sentence = get_sentence(mlf_dir / mlf_f_name, pms)

        i = 0

        for diphone, start, stop in sentence:
            signal_cut = get_signal_cut(signal, start, stop)
            if len(signal_cut) <= MIN_LENGTH:
                i += 1
                continue

            signal_cut = add_fade(signal_cut)

            sp_unit = SpeechUnit(signal_cut)

            if i > 0:
                left_diphone, _, _ = sentence[i - 1]
                sp_unit.left_phoneme = left_diphone[0]
            if i < len(sentence) - 1:
                right_diphone, _, _ = sentence[i + 1]
                sp_unit.right_phoneme = right_diphone[1]

            if diphone not in inv:
                inv[diphone] = []

            inv[diphone].append(sp_unit)

            i += 1

    # for key in inv:
    #     random.shuffle(inv[key])

    with open(inv_f_name / "inventory.plk", 'wb') as fw:
        plk.dump(inv, fw)

    phonemes_sim = get_phonemes_similarity()

    with open(inv_f_name / "phonemes_sim.plk", 'wb') as fw:
        plk.dump(phonemes_sim, fw)


def get_phonemes_similarity():
    phonemes_sim = dict()

    for phon_1 in ALPHABET:
        for phon_2 in ALPHABET:
            phonemes_sim[(phon_1, phon_2)] = 1.0

    for i, sim_level in enumerate(SIMILARITY):
        loss = SIMILARITY_LOSS[i]
        for instance in sim_level:
            for phon_1 in instance:
                for phon_2 in instance:
                    phonemes_sim[(phon_1, phon_2)] = loss

    for phon_1 in ALPHABET:
        phonemes_sim[(phon_1, phon_1)] = 0.0

    # # Vowel + X
    # for phon_1 in VOWELS:
    #     for phon_2 in VOWELS:
    #         if phon_1 == phon_2:
    #             phonemes_sim[(phon_1, phon_2)] = 0.0  # equal phonemes
    #         elif phon_1.lower() == phon_2.lower():
    #             phonemes_sim[(phon_1, phon_2)] = 0.25  # (long / short) vowel pairs
    #         else:
    #             phonemes_sim[(phon_1, phon_2)] = 0.5  # rest of vowel pairs
    #
    #     for phon_2 in UNVOICED_CONSONANTS + VOICED___CONSONANTS + special_chars:
    #         phonemes_sim[(phon_1, phon_2)] = 1.0  # different pairs
    #
    # # Unvoiced consonant + X
    # for phon_1 in UNVOICED_CONSONANTS:
    #     for phon_2 in UNVOICED_CONSONANTS:
    #         if phon_1 == phon_2:
    #             phonemes_sim[(phon_1, phon_2)] = 0.0  # equal phonemes
    #         else:
    #             phonemes_sim[(phon_1, phon_2)] = 0.5  # unvoiced consonants pairs
    #
    #     for phon_2 in VOWELS + VOICED___CONSONANTS + special_chars:
    #         phonemes_sim[(phon_1, phon_2)] = 1.0  # different pairs
    #
    # # Voiced consonant + X
    # for phon_1 in VOICED___CONSONANTS:
    #     for phon_2 in VOICED___CONSONANTS:
    #         if phon_1 == phon_2:
    #             phonemes_sim[(phon_1, phon_2)] = 0.0  # equal phonemes
    #         else:
    #             phonemes_sim[(phon_1, phon_2)] = 0.5  # voiced consonants pairs
    #
    #     for phon_2 in VOWELS + UNVOICED_CONSONANTS + special_chars:
    #         phonemes_sim[(phon_1, phon_2)] = 1.0  # different pairs
    #
    # # Special characters + X
    # for phon_1 in special_chars:
    #     for phon_2 in special_chars:
    #         if phon_1 == phon_2:
    #             phonemes_sim[(phon_1, phon_2)] = 0.0  # equal phonemes
    #         else:
    #             phonemes_sim[(phon_1, phon_2)] = 0.5  # special chars pairs
    #
    #     for phon_2 in VOWELS + UNVOICED_CONSONANTS + VOICED___CONSONANTS:
    #         phonemes_sim[(phon_1, phon_2)] = 1.0  # different pairs

    return phonemes_sim


def load_inventory(dir):
    with open(dir / "inventory.plk", 'rb') as fr:
        inv = plk.load(fr)
    return inv


def load_phonemes_sim(dir):
    with open(dir / "phonemes_sim.plk", 'rb') as fr:
        phonemes_sim = plk.load(fr)
    return phonemes_sim


# wavfile.write(DATA_DIR / OUT / "test.wav", sample_rate, signal_cut)

if __name__ == '__main__':
    mlf_dir = DATA_DIR / MLF
    pm_dir = DATA_DIR / PM
    spc_dir = DATA_DIR / SPC
    inv_dir = DATA_DIR / PREP

    create_inventory(mlf_dir, pm_dir, spc_dir, inv_dir)

    # analyse_phones_lengths()
