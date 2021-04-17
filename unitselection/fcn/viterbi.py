import numpy as np
from scipy.io import wavfile
from unitselection.fcn.constants import *

def get_existing_seq(sentence, inv):
    """
    Replaces non existing diphones by relatively similar existing option.
    """
    diphone_seq = []

    for diphone in sentence:
        # Equal diphone
        if diphone in inv:
            diphone_seq.append(diphone)
            continue

        # Very similar diphone
        sim_diphone = diphone[0] + diphone[1].swapcase()
        if sim_diphone in inv:
            diphone_seq.append(sim_diphone)
            continue
        sim_diphone = diphone[0].swapcase() + diphone[1]
        if sim_diphone in inv:
            diphone_seq.append(sim_diphone)
            continue
        sim_diphone = diphone[0].swapcase() + diphone[1].swapcase()
        if sim_diphone in inv:
            diphone_seq.append(sim_diphone)
            continue

    return diphone_seq


def get_empty_target_loss(sentence, inv):
    empty_target_loss = []

    for diphone in sentence:
        loss_vect = np.zeros((len(inv[diphone]), 1))
        empty_target_loss.append(loss_vect)

    return empty_target_loss


def get_pred_state_ref(sentence, inv):
    pred_state_ref = []

    for diphone in sentence:
        loss_vect = -np.ones((len(inv[diphone]),)).astype('int32')
        pred_state_ref.append(loss_vect)

    return pred_state_ref


def get_target_loss(sentence, inv, phonemes_sim):
    target_loss = get_empty_target_loss(sentence, inv)

    for i, diphone in enumerate(sentence):

        alternatives = inv[diphone]

        # Surrounding diphones loss
        if i > 0:
            real_left_phoneme = sentence[i - 1][0]
            alter_left_phonemes = [unit.left_phoneme for unit in alternatives]
            left_phoneme_losses = [phonemes_sim[(real_left_phoneme, l_ph)] for l_ph in alter_left_phonemes]
            target_loss[i] += np.expand_dims(np.array(left_phoneme_losses), axis=1)

        if i < len(sentence) - 1:
            real_right_phoneme = sentence[i + 1][1]
            alter_right_phonemes = [unit.right_phoneme for unit in alternatives]
            right_phoneme_losses = [phonemes_sim[(real_right_phoneme, r_ph)] for r_ph in alter_right_phonemes]
            target_loss[i] += np.expand_dims(np.array(right_phoneme_losses), axis=1)

    return target_loss


def cartesian_add(a, b):
    """
    Performs special cartesian addition operation.
    Assumes that a.shape = (N, 1) and b.shape = (1, M)
    """
    a = np.repeat(a, b.shape[1], axis=1)
    b = np.repeat(b, a.shape[0], axis=0)
    return a + b


def get_optimal_signal(sentence, inv, phonemes_sim):
    sentence = get_existing_seq(sentence, inv)
    target_loss = get_target_loss(sentence, inv, phonemes_sim)
    cum_loss = get_empty_target_loss(sentence, inv)
    pred_state_ref = get_pred_state_ref(sentence, inv)

    cum_loss[0] = target_loss[0]

    for i in range(1, len(target_loss)):
        prev_loss = cum_loss[i - 1]
        this_loss = target_loss[i]

        best_prev_state = np.argmin(prev_loss)
        pred_state_ref[i] *= -best_prev_state

        best_prev_loss = prev_loss[best_prev_state]
        cum_loss[i] = this_loss + best_prev_loss

    signal = []
    last_diphone = sentence[-1]

    best_last_i = np.argmin(cum_loss[-1])
    signal.append(inv[last_diphone][best_last_i].signal)

    for i in range(len(target_loss) - 2, -1, -1):
        best_last_i = pred_state_ref[i + 1][best_last_i]
        last_diphone = sentence[i]
        signal.append(inv[last_diphone][best_last_i].signal)

    signal = signal[::-1]

    return signal


if __name__ == '__main__':
    pass
