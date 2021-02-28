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
    """Repeats all replacements defined in ´REGEX_RULES´ until the syntax of the  phonetic transcription is correct."""
    for regex in REGEX_RULES:
        txt = re.sub(regex, REGEX_RULES[regex], txt)

    return txt


def chain_replacement(txt):
    """Process the input text (backwards) character by character
    and applies replacements based on the phonetic chain-type rules."""

    list_txt = list(txt)

    matches = re.finditer(CHAIN_REGIONS_REGEX, txt)

    matches_positions = [(match.start(), match.end()) for match in matches]

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


def process_file(file_path=Path("../data/test/vety_HDS.ortho.txt")):
    """Creates file with the translation of the content of the input file."""
    txt = load_text(file_path)
    txt = translate(txt)

    # Build the output path
    file_name = file_path.name.replace("ortho", "phntrn")
    output_path = file_path.parent.parent / "output" / file_name

    # Save the output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(txt)
