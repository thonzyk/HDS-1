"""Diphone inventory assembly"""
import argparse
import bisect
import os
import pickle as plk
from pathlib import Path

from scipy.io import wavfile

from unitselection.fcn.constants import *
from unitselection.fcn.prepare_data import split_mlf
from unitselection.fcn.speech_unit import SpeechUnit

parser = argparse.ArgumentParser()
parser.add_argument('hds_data_dir', metavar='HDS_DATA_DIR', type=str, help='HDS data directory')


def get_pitch_marks(pm_f_name):
    """Returns list of pitch marks loaded from the input file."""
    pms = []
    with open(pm_f_name, 'r', encoding='utf-8') as pm_f:
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


def get_signal_cut(signal, start, stop):
    """Returns signal fragment cut by the start and stop time values."""
    start_i = round(start / SAMPLE_TIME)
    stop_i = round(stop / SAMPLE_TIME)

    return np.copy(signal[start_i:stop_i])


def nearest_pitchmark(pms, time):
    """Returns the pitch mark closest to the specified time."""
    pm_time_i = bisect.bisect_right(pms, (time,))
    time_pm = pms[pm_time_i][0]

    return time_pm


def add_fade(signal):
    """Returns the input signal with smoothed ends (with Hanning window)."""
    win_half = len(WINDOW) // 2
    signal[:win_half] *= WINDOW[:win_half]
    signal[-win_half:] *= WINDOW[-win_half:]

    return signal


def get_phonem(line):
    """Return phoneme data parsed from the input line."""
    line = line[:-1]
    items = line.split(' ')
    start = float(items[0]) * TIME_STEP
    stop = float(items[1]) * TIME_STEP
    center = (start + stop) / 2
    phoneme = items[2]

    return phoneme, start, stop, center


def get_sentence(mlf_f_name, pms):
    """Returns sentence data parsed from the input file with support of the given pitch marks."""
    sentence = []
    with open(mlf_f_name, 'r', encoding='utf-8') as mlf_f:
        first_line = True
        for line in mlf_f:
            if first_line:
                last_phoneme = '$'
                last_center = 0.0
                first_line = False
                continue
            phoneme, _, _, center = get_phonem(line)
            center = nearest_pitchmark(pms, center)
            sentence.append((last_phoneme + phoneme, max(last_center - FADE_TIME / 2, 0.0), center))
            last_center = center
            last_phoneme = phoneme

    return sentence


def load_unsel_feats(dir, sent_name):
    """Returns the unsel features for the specified sentence loaded from the given directory."""
    enrg_name = sent_name + ".enrg.txt"
    f0_name = sent_name + ".f0.txt"
    mfcc_name = sent_name + ".mfcc.txt"
    enrg = []
    f0 = []
    mfcc = []
    with open(dir / enrg_name, 'r') as fr:
        for line in fr:
            if line[0] != '|':
                continue
            line = line[:-1].replace(' ', '')
            items = line.split('|')
            enrg.append((float(items[1]), float(items[3])))
    with open(dir / f0_name, 'r') as fr:
        for line in fr:
            if line[0] != '|':
                continue
            line = line[:-1].replace(' ', '')
            items = line.split('|')
            f0.append((float(items[1]), float(items[3])))
    with open(dir / mfcc_name, 'r') as fr:
        for line in fr:
            if line[0] != '|':
                continue
            line = line[:-1].replace(' ', '')
            items = line.split('|')
            items = tuple([float(el) for el in items[1:-1]])
            mfcc.append(items)

    return enrg, f0, mfcc


def get_unsel_feats(t, enrg, f0, mfcc):
    """Returns the unsel features aligned to the pitch mark which is closest to the specified time."""
    enrg_i = bisect.bisect_right(enrg, (t,))
    enrg_in_time = enrg[enrg_i][1]
    f0_i = bisect.bisect_right(f0, (t,))
    f0_in_time = f0[f0_i][1]
    mfcc_i = bisect.bisect_right(mfcc, (t,))
    mfcc_in_time = mfcc[mfcc_i][1:]

    return enrg_in_time, f0_in_time, mfcc_in_time


def create_inventory(mlf_dir, pm_dir, spc_dir, inv_f_name, unsel_feats_dir):
    """Creates the diphone inventory from the given directories."""
    _, _, mlf_files = next(os.walk(mlf_dir))
    inv = dict()
    for mlf_f_name in mlf_files:
        # Load relevant data from mlf, pm, spc and unsel_feats directories
        sent_name = mlf_f_name[:-4]
        pm_name = sent_name + ".pm"
        spc_name = sent_name + ".wav"
        sample_rate, signal = wavfile.read(spc_dir / spc_name)
        signal = signal.astype('float32')
        pms = get_pitch_marks(pm_dir / pm_name)
        enrg, f0, mfcc = load_unsel_feats(unsel_feats_dir, sent_name)
        sentence = get_sentence(mlf_dir / mlf_f_name, pms)
        # Extract speech units (diphones) from the loaded sentence
        i = 0
        for diphone, start, stop in sentence:
            signal_cut = get_signal_cut(signal, start, stop)
            if len(signal_cut) <= MIN_LENGTH:
                i += 1
                continue
            signal_cut = add_fade(signal_cut)
            enrg_start, f0_start, mfcc_start = get_unsel_feats(start, enrg, f0, mfcc)
            enrg_stop, f0_stop, mfcc_stop = get_unsel_feats(stop, enrg, f0, mfcc)
            # Assembly of speech unit
            sp_unit = SpeechUnit(signal_cut, enrg_start, enrg_stop, f0_start, f0_stop, mfcc_start, mfcc_stop)
            sp_unit.sentence_position = i / len(sentence)
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

    with open(inv_f_name / INV, 'wb') as fw:
        plk.dump(inv, fw)
    phonemes_sim = get_phonemes_similarity()
    with open(inv_f_name / PHON_SIM, 'wb') as fw:
        plk.dump(phonemes_sim, fw)


def get_phonemes_similarity():
    """Returns dictionary of relative similarity loss between two phonemes."""
    phonemes_sim = dict()
    for phon_1 in ALPHABET:
        phonemes_sim[(phon_1, None)] = 2.0
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

    return phonemes_sim


def load_inventory(dir):
    """Loads the inventory file."""
    with open(dir / INV, 'rb') as fr:
        inv = plk.load(fr)
    return inv


def load_phonemes_sim(dir):
    """Loads the phonemes similarity file."""
    with open(dir / PHON_SIM, 'rb') as fr:
        phonemes_sim = plk.load(fr)
    return phonemes_sim


def inventory_create(hds_dir):
    """Creates the speech unit dictionary computed from the given ´hds_data´ directory."""
    mlf_dir = hds_dir / MLF
    if not os.path.exists(mlf_dir):
        os.mkdir(mlf_dir)
        split_mlf(hds_dir)
    pm_dir = hds_dir / PM
    spc_dir = hds_dir / SPC
    inv_dir = hds_dir / PREP
    if not os.path.exists(inv_dir):
        os.mkdir(inv_dir)
    unsel_feats_dir = hds_dir / UNS_FT

    create_inventory(mlf_dir, pm_dir, spc_dir, inv_dir, unsel_feats_dir)


if __name__ == '__main__':
    args = parser.parse_args()
    inventory_create(Path(args.hds_data_dir))
