"""Viterbi algorithm"""
from unitselection.fcn.constants import *

# Viterbi algorithm parameters - weights of different synthesis losses
SURROUNDING_WEIGHT = 1.0  # surrounding diphones
SENTENCE_POSITION_WEIGHT = 0.1  # relative position in sentence
ENRG_WEIGHT = 1.0  # concatenation of energy
F0_WEIGHT = 1.0  # concatenation of F0
MFCC_WEIGHT = 0.01  # concatenation of MFCC coefficients


def get_sim_diphone(diphone, inv):
    """Returns the most similar known diphone."""
    phon_1_sims = []
    phon_2_sims = []
    for i, sim_level in enumerate(SIMILARITY[::-1]):
        for instance in sim_level:
            if diphone[0] in instance:
                for phon in instance:
                    phon_1_sims.append(phon)
                    sim_diphone = phon + diphone[1]
                    if sim_diphone in inv:
                        return sim_diphone
            if diphone[1] in instance:
                for phon in instance:
                    phon_2_sims.append(phon)
                    sim_diphone = diphone[0] + phon
                    if sim_diphone in inv:
                        return sim_diphone

    for phon_1 in phon_1_sims:
        for phon_2 in phon_2_sims:
            sim_diphone = phon_1 + phon_2
            if sim_diphone in inv:
                return sim_diphone

    print(f"Similar diphone not found for {diphone}.")
    return None


def get_existing_seq(sentence, inv):
    """Replaces non existing diphones by relatively similar existing option."""
    diphone_seq = []
    for diphone in sentence:
        # Equal diphone
        if diphone in inv:
            diphone_seq.append(diphone)
            continue
        sim_diphone = get_sim_diphone(diphone, inv)
        if sim_diphone is not None:
            diphone_seq.append(sim_diphone)

    return diphone_seq


def get_empty_target_loss(sentence, inv):
    """Returns list of empty target loss vectors."""
    empty_target_loss = []
    for diphone in sentence:
        loss_vect = np.zeros((len(inv[diphone]), 1))
        empty_target_loss.append(loss_vect)

    return empty_target_loss


def get_pred_state_ref(sentence, inv):
    """Returns list of empty reference previous state indexes (vectors)."""
    pred_state_ref = []
    for diphone in sentence:
        loss_vect = -np.ones((len(inv[diphone]),)).astype('int32')
        pred_state_ref.append(loss_vect)

    return pred_state_ref


def get_target_loss(sentence, inv, phonemes_sim):
    """Computes the target loss of each alternative element."""
    target_loss = get_empty_target_loss(sentence, inv)
    for i, diphone in enumerate(sentence):
        alternatives = inv[diphone]
        # Sentence position loss
        real_sentence_position = i / len(sentence)
        alter_sentence_positions = np.array(list(map(lambda x: x.sentence_position, alternatives)))
        target_loss[i] += np.expand_dims(np.abs(alter_sentence_positions - real_sentence_position),
                                         axis=1) * SENTENCE_POSITION_WEIGHT
        # Surrounding diphones loss
        if i > 0:
            real_left_phoneme = sentence[i - 1][0]
            alter_left_phonemes = [unit.left_phoneme for unit in alternatives]
            left_phoneme_losses = [phonemes_sim[(real_left_phoneme, l_ph)] for l_ph in alter_left_phonemes]
            target_loss[i] += np.expand_dims(np.array(left_phoneme_losses), axis=1) * SURROUNDING_WEIGHT

        if i < len(sentence) - 1:
            real_right_phoneme = sentence[i + 1][1]
            alter_right_phonemes = [unit.right_phoneme for unit in alternatives]
            right_phoneme_losses = [phonemes_sim[(real_right_phoneme, r_ph)] for r_ph in alter_right_phonemes]
            target_loss[i] += np.expand_dims(np.array(right_phoneme_losses), axis=1) * SURROUNDING_WEIGHT

    return target_loss


def get_empty_concat_loss(sentence, inv):
    """Returns list of empty concatenation loss matrices."""
    empty_concat_loss = []
    for i in range(1, len(sentence)):
        prev_diphone = sentence[i - 1]
        this_diphone = sentence[i]
        loss_mat = np.zeros((len(inv[prev_diphone]), len(inv[this_diphone])))
        empty_concat_loss.append(loss_mat)

    return empty_concat_loss


def get_f0_loss_mat(prev_alter, this_alter):
    """Returns F0 concatenation loss."""
    prev_alter = np.repeat(prev_alter, this_alter.shape[1], axis=1)
    this_alter = np.repeat(this_alter, prev_alter.shape[0], axis=0)
    loss_mat = np.abs(prev_alter - this_alter)

    return loss_mat * F0_WEIGHT


def get_enrg_loss_mat(prev_alter, this_alter):
    """Returns energy concatenation loss."""
    prev_alter = np.repeat(prev_alter, this_alter.shape[1], axis=1)
    this_alter = np.repeat(this_alter, prev_alter.shape[0], axis=0)
    loss_mat = np.abs(prev_alter - this_alter)

    return loss_mat * ENRG_WEIGHT


def get_mfcc_loss_mat(prev_alter, this_alter):
    """Returns MFCC coeficients concatenation loss."""
    prev_alter = np.repeat(prev_alter, this_alter.shape[1], axis=1)
    this_alter = np.repeat(this_alter, prev_alter.shape[0], axis=0)
    loss_mat = prev_alter - this_alter
    loss_mat = np.square(loss_mat)
    loss_mat = np.sum(loss_mat, axis=2)
    loss_mat = np.sqrt(loss_mat)

    return loss_mat * MFCC_WEIGHT


def get_concat_loss(sentence, inv):
    """Computes the concatenation loss for each consecutive diphone pair alternatives."""
    concat_loss = get_empty_concat_loss(sentence, inv)
    for i in range(1, len(sentence)):
        prev_alternatives = inv[sentence[i - 1]]
        this_alternatives = inv[sentence[i]]
        # Energy loss
        prev_enrg_alter = np.expand_dims(np.array(list(map(lambda x: x.enrg_stop, prev_alternatives))), axis=1)
        this_enrg_alter = np.expand_dims(np.array(list(map(lambda x: x.enrg_start, this_alternatives))), axis=0)
        enrg_loss_mat = get_enrg_loss_mat(prev_enrg_alter, this_enrg_alter)
        # MFCC loss
        prev_mfcc_alter = np.expand_dims(np.array(list(map(lambda x: x.mfcc_stop, prev_alternatives))), axis=1)
        this_mfcc_alter = np.expand_dims(np.array(list(map(lambda x: x.mfcc_start, this_alternatives))), axis=0)
        mfcc_loss_mat = get_mfcc_loss_mat(prev_mfcc_alter, this_mfcc_alter)
        # F0 loss
        prev_f0_alter = np.expand_dims(np.array(list(map(lambda x: x.f0_stop, prev_alternatives))), axis=1)
        this_f0_alter = np.expand_dims(np.array(list(map(lambda x: x.f0_start, this_alternatives))), axis=0)
        f0_loss_mat = get_f0_loss_mat(prev_f0_alter, this_f0_alter)
        # Total concatenation loss
        concat_loss[i - 1] += enrg_loss_mat + f0_loss_mat + mfcc_loss_mat

    return concat_loss


def merge_target_and_concat_loss(prev_loss, this_target_loss, this_concat_loss):
    """Returns added target and concatenation losses."""
    prev_loss = np.repeat(prev_loss, this_target_loss.shape[1], axis=1)
    this_target_loss = np.repeat(this_target_loss, prev_loss.shape[0], axis=0)

    return this_concat_loss + prev_loss + this_target_loss


def get_optimal_signal(sentence, inv, phonemes_sim):
    """Computes loss of all possible sequence alternatives and returns the best one."""
    # Prepare the sentence and compute marginal losses
    sentence = get_existing_seq(sentence, inv)
    target_loss = get_target_loss(sentence, inv, phonemes_sim)
    concat_loss = get_concat_loss(sentence, inv)
    cum_loss = get_empty_target_loss(sentence, inv)
    pred_state_ref = get_pred_state_ref(sentence, inv)
    cum_loss[0] += target_loss[0]
    # Compute the accumulated loss (Viterbi algorithm)
    for i in range(1, len(target_loss)):
        prev_loss = cum_loss[i - 1]
        this_target_loss = np.transpose(target_loss[i])
        this_concat_loss = concat_loss[i - 1]
        loss = merge_target_and_concat_loss(prev_loss, this_target_loss, this_concat_loss)
        best_prev_state = np.argmin(loss, axis=0)
        pred_state_ref[i] *= -best_prev_state
        cum_loss[i] += np.expand_dims(loss[list(best_prev_state), [*range(this_target_loss.size)]], axis=1)

    # The best sequence assembly (in backwards)
    signal = []
    last_diphone = sentence[-1]
    best_last_i = np.argmin(cum_loss[-1])
    signal.append(inv[last_diphone][best_last_i].signal)
    for i in range(len(target_loss) - 2, -1, -1):
        best_last_i = pred_state_ref[i + 1][best_last_i]
        last_diphone = sentence[i]
        signal.append(inv[last_diphone][best_last_i].signal)
    # Flip the reverse assembled sequence of signal fragments
    signal = signal[::-1]

    return signal
