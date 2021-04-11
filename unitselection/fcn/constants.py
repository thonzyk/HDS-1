from pathlib import Path
import numpy as np

DATA_DIR = Path("D:/ML-Data/hds_data/")

ALPHABET = ['$', 'T', 'I', 'm', 'p', 'Q', 'e', 'c', 't', 'k', 'i', 'J', 's', 'n', 'A', 'u', '!', 'o', 'r', 'h', 'y',
            'd', 'f', 'E', 'a', 'D', 'S', 'v', 'l', 'U', '#', 'b', 'z', 'j', 'C', 'Z', 'g', '%', 'R', 'N', 'x', 'O',
            'w', 'Y', 'F', 'W', 'M']
PM = "pm"
SPC = "spc"
MLF = "mlf"
TXT_FON = "texty_fonetika"
UNS_FT = "unsel-feats"
OUT = "out"
PREP = "prep"

INV = "inventory.plk"

ORIG_MLF = "phnalign.mlf"

TIME_STEP = 1.0e-7

FADE_TIME = 0.01


SAMPLE_RATE = 16000
SAMPLE_TIME = 1.0 / SAMPLE_RATE
MIN_LENGTH = np.ceil(2 * FADE_TIME * SAMPLE_RATE)
WINDOW = np.hanning(MIN_LENGTH)

FADE_LEN = round(FADE_TIME * SAMPLE_RATE)

MAX_PHONEME_LEN_SEC = 0.5
