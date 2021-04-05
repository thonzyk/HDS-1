"""Algorithm rules"""
from .constants import *

# TODO-optimize: use regex for equivalent replacements
SIMPLE_RULES = {
    'ni': 'Ji',
    'ní': 'JI',
    'ti': 'Ti',
    'tí': 'TI',
    'di': 'Di',
    'dí': 'DI',

    'y': 'i',
    'ý': 'I',
    'í': 'I',
    'é': 'E',
    'á': 'A',
    'ó': 'O',
    'ú': 'U',
    'ů': 'U',

    'ou': 'y',
    'au': 'Y',
    'eu': 'F',

    'š': 'S',
    'ť': 'T',
    'ň': 'J',
    'ď': 'D',
    'ž': 'Z',
    'č': 'C',
    'ř': 'R',

    'dz': 'w',
    'dZ': 'W',

    '\n': '\n|$|',

    'ch': 'x',

    'dě': 'De',
    'tě': 'Te',
    'ně': 'Je',
    'mě': 'mJe',
    'ě': 'je',

    'js': 's',

    '\t': '',

    '. ': '|$|',
    '.': '|$|',
    '; ': '|$|',
    ';': '|$|',

    ', ': '|#|',
    ',': '|#|',

    ' ': '|',

    'x|': 'G|',
    'h|': 'G|',

    '|a': '|!a',
    '|e': '|!e',
    '|i': '|!i',
    '|o': '|!o',
    '|u': '|!u',

    '|A': '|!A',
    '|E': '|!E',
    '|I': '|!I',
    '|O': '|!O',
    '|U': '|!U',

}

REGEX_RULES = {
    '([' + UNVOICED_CHARS + '])' + 'R': '\\1Q',
    '([' + UNVOICED_CHARS + '])' + 'm' + '([\\|' + UNVOICED_CHARS + '])': '\\1H\\2',
    '([' + UNVOICED_CHARS + '])' + 'l' + '([\\|' + UNVOICED_CHARS + '])': '\\1L\\2',
    '([' + CONSONANTS + '])' + 'r' + '([\\|' + CONSONANTS + '])': '\\1P\\2',
    '([' + UNVOICED_CHARS + '])' + 'm' + '([\\|' + '])': '\\1H\\2',
    '([' + CONSONANTS + '][' + VOWELS + '])' + 'd' + '(\\|)': '\\1t\\2',
    '([' + CONSONANTS + ']\\|)' + 'z': '\\1s',
}
