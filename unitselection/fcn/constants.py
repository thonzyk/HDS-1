"""Constants"""
import numpy as np

# All possible characters in phonetic transcription
ALPHABET = ['$', 'T', 'I', 'm', 'p', 'Q', 'e', 'c', 't', 'k', 'i', 'J', 's', 'n', 'A', 'u', '!', 'o', 'r', 'h', 'y',
            'd', 'f', 'E', 'a', 'D', 'S', 'v', 'l', 'U', '#', 'b', 'z', 'j', 'C', 'Z', 'g', '%', 'R', 'N', 'x', 'O',
            'w', 'Y', 'F', 'W', 'M']

# Characters grouped by 3 levels of similarity
SIMILARITY = [
    ['aeiouAEIOUyYF', 'bdDgvzZhwWR', 'ptTkfsSxcCQ', 'mnNljrLP'],
    ['yYFuU', 'xGh', 'Ya', 'oy', 'eF'],
    ['iI', 'eE', 'aA', 'oO', 'uU', 'sz', 'ZS', 'xG', 'fv', 'bp', 'td', 'DT', 'gk', 'mn', 'Jj', 'Nn', 'mMH', '$#%', 'Ll',
     'Pr']
]
# Loss of each similarity level
SIMILARITY_LOSS = [0.75, 0.5, 0.25]
# Directory name constants
PM = "pm"
SPC = "spc"
MLF = "mlf"
TXT_FON = "texty_fonetika"
UNS_FT = "unsel-feats"
OUT = "out"
PREP = "prep"
INV = "inventory.plk"
PHON_SIM = "phonemes_sim.plk"
ORIG_MLF = "phnalign.mlf"
# Numeric constants
TIME_STEP = 1.0e-7  # time step of the original MLF file [s]
FADE_TIME = 0.01  # choosen fade in/out lenght [s]
SAMPLE_RATE = 16000
SAMPLE_TIME = 1.0 / SAMPLE_RATE
MIN_LENGTH = np.ceil(2 * FADE_TIME * SAMPLE_RATE)  # minimal length of speech unit
WINDOW = np.hanning(MIN_LENGTH)  # smoothing window for speech units concatenation
FADE_LEN = round(FADE_TIME * SAMPLE_RATE)
