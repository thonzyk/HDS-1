class SpeechUnit:
    def __init__(self, signal):
        self.signal = signal

        # Target loss params
        self.left_phoneme = None  # difference from dictionary
        self.right_phoneme = None  # difference from dictionary
        self.sentence_type = None  # direct comparison
        self.word_position = None  # direct difference
        self.sentence_position = None  # direct difference
        self.word_length = None  # direct difference

        # Concatenate loss params
