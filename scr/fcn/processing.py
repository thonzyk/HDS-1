"""Core source code of the algorithm"""
from pathlib import Path

from .constants import *


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
    return txt


def grind(txt):
    """Performs final feed-forward modifications."""
    txt = "|$|" + txt[:-3]
    return txt


def translate(txt):
    """Takes a plain czech text as an input and returns its phonetic transcription."""
    txt = txt.lower()
    txt = simple_replacement(txt)
    txt = regex_replacement(txt)
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
