class SpeechUnit:
    """Storage of important attributes of speech unit for correct integration into speech synthesis."""

    def __init__(self, signal, enrg_start, enrg_stop, f0_start, f0_stop, mfcc_start, mfcc_stop):
        self.signal = signal

        # Target loss params
        self.left_phoneme = None
        self.right_phoneme = None
        self.sentence_type = None
        self.word_position = None
        self.sentence_position = None
        self.word_length = None

        # Concatenate loss params
        self.enrg_start = enrg_start
        self.enrg_stop = enrg_stop
        self.f0_start = f0_start
        self.f0_stop = f0_stop
        self.mfcc_start = mfcc_start
        self.mfcc_stop = mfcc_stop
