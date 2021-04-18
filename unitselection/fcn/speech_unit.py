class SpeechUnit:
    def __init__(self, signal, enrg_start, enrg_stop, f0_start, f0_stop, mfcc_start, mfcc_stop):
        self.signal = signal

        # Target loss params
        self.left_phoneme = None  # difference from dictionary
        self.right_phoneme = None  # difference from dictionary
        self.sentence_type = None  # direct comparison
        self.word_position = None  # direct difference
        self.sentence_position = None  # direct difference
        self.word_length = None  # direct difference

        # Concatenate loss params
        self.enrg_start = enrg_start
        self.enrg_stop = enrg_stop
        self.f0_start = f0_start
        self.f0_stop = f0_stop
        self.mfcc_start = mfcc_start
        self.mfcc_stop = mfcc_stop
