"""Project constants"""

# Original constants
UNVOICED_CONSONANTS = "ptTkfsSxcCQ"
VOICED_P_CONSONANTS = "bdDgvzZhwWR"  # voiced pair consonants
VOICED_N_CONSONANTS = "mnNljr"  # voiced non-pair consonants
VOWELS = 'aeiouAEIOU'
RECESSIVE_CHARS = "v"  # characters which are excluded when the dominant character search is performed

# Concatenated versions of original constants
VOICED___CONSONANTS = VOICED_P_CONSONANTS + VOICED_N_CONSONANTS
CONSONANTS = UNVOICED_CONSONANTS + VOICED___CONSONANTS
VOICED_CHARS = VOICED___CONSONANTS + VOWELS
UNVOICED_CHARS = UNVOICED_CONSONANTS
PAIR_CONSONANTS = UNVOICED_CONSONANTS + VOICED_P_CONSONANTS

# Regexes
CHAIN_REGIONS_REGEX = '([' + PAIR_CONSONANTS + ']+' + '[\\|]?' + '[' + PAIR_CONSONANTS + ']+)'

# Maps / Dictionaries
VOICED_TO_UNVOICED = {
    'b': 'p',
    'd': 't',
    'D': 'T',
    'g': 'k',
    'v': 'f',
    'z': 's',
    'Z': 'S',
    'h': 'x',
    'w': 'c',
    'W': 'C',
    'R': 'R',  # TODO-refactoring: remove this hack
}
UNVOICED_TO_VOICED = {
    'p': 'b',
    't': 'd',
    'T': 'D',
    'k': 'g',
    'f': 'v',
    's': 'z',
    'S': 'Z',
    'x': 'h',
    'c': 'w',
    'C': 'W',
    'Q': 'Q',  # TODO-refactoring: remove this hack
}
