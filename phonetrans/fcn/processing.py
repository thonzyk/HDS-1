"""Core source code of the algorithm"""
import re
from pathlib import Path

from .rules import *


def load_text(file_path):
    """Loads and returns the content of specified text file."""
    f = open(file_path, "r", encoding='utf-8')
    txt = f.read()
    f.close()
    return txt


def simple_replacement(txt):
    """Performs all replacements defined in ´SIMPLE_RULES´ dictionary."""
    for character in SIMPLE_RULES:
        txt = txt.replace(character, SIMPLE_RULES[character])

    return txt


def regex_replacement(txt):
    """Performs all replacements defined in ´REGEX_RULES´ dictionary."""
    for regex in REGEX_RULES:
        txt = re.sub(regex, REGEX_RULES[regex], txt)

    return txt


def chain_replacement(txt):
    """Finds all the occurrences of pair consonants chains and applies relevant replacements."""

    # Create list-type copy of original text for swift character replacements
    list_txt = list(txt)

    # Find all wanted chains
    matches = re.finditer(CHAIN_REGIONS_REGEX, txt)
    matches_positions = [(match.start(), match.end()) for match in matches]

    # Process each chain
    for match in matches_positions:
        chain = txt[match[0]:match[1]]
        dominant_char = chain[-1]

        if dominant_char in RECESSIVE_CHARS:
            continue
        elif dominant_char in VOICED_CHARS:
            for i in range(match[0], match[1]):
                if txt[i] in PAIR_CONSONANTS and txt[i] in UNVOICED_CONSONANTS:
                    list_txt[i] = UNVOICED_TO_VOICED[txt[i]]

        elif dominant_char in UNVOICED_CHARS:
            for i in range(match[0], match[1]):
                if txt[i] in PAIR_CONSONANTS and txt[i] in VOICED_P_CONSONANTS:
                    list_txt[i] = VOICED_TO_UNVOICED[txt[i]]

    return "".join(list_txt)


def grind(txt):
    """Performs final feed-forward modifications."""
    txt = "|$|" + txt[:-3]
    return txt


def translate(txt):
    """Takes a plain czech text as an input and returns its phonetic transcription."""
    txt = txt.lower()
    txt = simple_replacement(txt)
    txt = regex_replacement(txt)
    txt = chain_replacement(txt)
    txt = grind(txt)
    return txt


def transcribe_file(input_path, output_path):
    """Creates file with the translation of the content of the input file."""
    input_path = Path(input_path)

    txt = load_text(input_path)
    txt = translate(txt)

    # If output path is not specified, it is build based on the input path
    if output_path is None:
        file_name = input_path.name.replace("ortho", "phntrn")
        output_path = input_path.parent.parent / "output" / file_name

    # Save the output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(txt)
