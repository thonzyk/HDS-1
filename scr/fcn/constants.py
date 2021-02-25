EPA = "ieaouIEAOUyYFfvszSZxhlrRjPbtdDkgmnJcCwWNMGQPLH!@$#%"

# TODO-optimize: use regex for equivalent replacements
SIMPLE_RULES = {

    'ni': 'Ji',
    'ní': 'JI',

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

    'ň': 'J',

    '\n': '\n|$|',

    'ch': 'x',
    'x ': 'G ',
    'x.': 'G.',
    'x,': 'G,',
    'x;': 'G;',

    '\t': '',

    '. ': '|$|',
    '.': '|$|',
    '; ': '|$|',
    ';': '|$|',

    ', ': '|#|',
    ',': '|#|',

    ' ': '|',

    '|a': '|!a',
    '|e': '|!e',
    '|i': '|!i',
    '|o': '|!o',
    '|u': '|!u',

}

REGEX_RULES = {

}
