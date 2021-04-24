"""Speech concatenation"""
from scipy.io import wavfile

from unitselection.fcn.inventory_diphone import load_inventory, load_phonemes_sim
from unitselection.fcn.viterbi import *


def concat_diphones(diphones):
    """Concatenates signal fragments into the whole sentence."""
    # Prepare array for result
    phon_lens = [len(element) for element in diphones]
    total_len = sum(phon_lens)
    sound = np.zeros((total_len,))
    # Perform the concatenation
    prev_sound_i = 0
    sound_i = prev_sound_i
    for phone in diphones:
        sound_i += len(phone)
        sound[prev_sound_i:sound_i] += phone
        sound_i -= FADE_LEN
        prev_sound_i = sound_i

    return sound.astype('int16')


def to_diphones(sentence):
    """Takes string with phonetic transcription as an input and returns equivalent diphone sequence."""
    new_sentence = []
    last_phoneme = sentence[0]
    for phoneme in sentence[1:]:
        diphone = last_phoneme + phoneme
        last_phoneme = phoneme
        new_sentence.append(diphone)

    return new_sentence


def get_best_sequence(sentence, inv, phonemes_sim):
    """Returns the best sequence of diphones signal according to implemented viterbi algorithm."""
    return get_optimal_signal(sentence, inv, phonemes_sim)


def synthetize_speech(input_file, hds_dir, out_dir):
    """Creates .wav file for each line of the ´input_file´ with synthetized sentence and saves these files into ´out_dir´.
    The ´hds_dir´ is necessary to load supportive files."""
    inv = load_inventory(hds_dir / PREP)
    phonemes_sim = load_phonemes_sim(hds_dir / PREP)

    with open(input_file, 'r', encoding='utf-8') as fr:
        lines = fr.read().splitlines()
        for i, line in enumerate(lines):
            # Remove unwanted characters
            line = line.replace('|', '')
            line = line.replace('#', '')
            line = line.replace('?', '')
            # Process the sentence
            diphones = to_diphones(line)
            sequence = get_best_sequence(diphones, inv, phonemes_sim)
            sound = concat_diphones(sequence)
            f_name = str(i + 1).zfill(4) + ".wav"
            wavfile.write(out_dir / f_name, SAMPLE_RATE, sound)
