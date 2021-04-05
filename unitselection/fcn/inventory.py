import os
from unitselection.fcn.constants import *
import pickle as plk
from scipy.io import wavfile
import matplotlib
from matplotlib import pyplot as plt
import bisect

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
            time = float(items[0])
            typ = items[-1]
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


def get_signal_cut(signal, sample_time, start, stop, pms):
    """
    :param signal: 1D ndarray representing the signal amplitude time series
    :param sample_time: signal sample time [second]
    :param start: start of the cut time [seconds]
    :param stop: start of the cut time [seconds]
    :param pms: pitch marks list
    :return: subsignal cut out of the original signal based on the given time window corrected by the pitch marks.
    """
    # TODO-critical: add pitch mark correction

    pm_start_i = bisect.bisect_right(pms, (start,))
    start_pm = pms[pm_start_i][0]

    pm_stop_i = bisect.bisect_right(pms, (stop,))
    stop_pm = pms[pm_stop_i][0]

    start_i = round(start_pm / sample_time)
    stop_i = round(stop_pm / sample_time)

    return signal[start_i:stop_i]


def add_fade(signal, window):
    """
    :param signal: 1D ndarray representing the signal amplitude time series
    :param signal: window used to perform fade
    :return: signal with fade-in and fade-out regions
    """

    win_half = len(window) // 2

    signal[:win_half] *= window[:win_half]
    signal[-win_half:] *= window[-win_half:]

    return signal


def create_inventory(mlf_dir, pm_dir, spc_dir, inv_f_name):
    _, _, mlf_files = next(os.walk(mlf_dir))

    inv = dict()

    for chr in ALPHABET:
        inv[chr] = []

    for mlf_f_name in mlf_files:
        pm_name = mlf_f_name[:-4] + ".pm"
        spc_name = mlf_f_name[:-4] + ".wav"

        with open(spc_dir / spc_name, 'r', encoding='utf-8') as spc_f:
            sample_rate, signal = wavfile.read(DATA_DIR / SPC / "Sentence00001.wav")

        signal = signal.astype('float32')
        # sample_time = 1.0 / sample_rate
        # min_length = 2 * FADE_TIME * sample_rate
        # window = np.hanning(min_length)
        pms = get_pitch_marks(pm_dir / pm_name)

        with open(mlf_dir / mlf_f_name, 'r', encoding='utf-8') as mlf_f:
            for line in mlf_f:
                line = line[:-1]
                items = line.split(' ')
                start = int(items[0]) * TIME_STEP
                stop = int(items[1]) * TIME_STEP
                phonem = items[2]
                signal_cut = get_signal_cut(signal, SAMPLE_TIME, start, stop, pms)

                if len(signal_cut) <= MIN_LENGTH:
                    continue

                signal_cut = add_fade(signal_cut, WINDOW)

                # if phonem not in inv:
                #     inv[phonem] = []

                inv[phonem].append(signal_cut)

    with open(DATA_DIR / PREP / "inventory.plk", 'wb') as fw:
        plk.dump(inv, fw)

    print()


def load_inventory(path=DATA_DIR / PREP / "inventory.plk"):
    with open(DATA_DIR / PREP / "inventory.plk", 'rb') as fr:
        inv = plk.load(fr)
    return inv


# wavfile.write(DATA_DIR / OUT / "test.wav", sample_rate, signal_cut)

if __name__ == '__main__':
    mlf_dir = DATA_DIR / MLF
    pm_dir = DATA_DIR / PM
    spc_dir = DATA_DIR / SPC
    inv_f_name = DATA_DIR / PREP / "inventory.plk"

    create_inventory(mlf_dir, pm_dir, spc_dir, inv_f_name)

    # analyse_phones_lengths()
