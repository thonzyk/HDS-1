"""Data preparation"""
from unitselection.fcn.constants import *


def is_data_line(line):
    return line[0].isnumeric()


def is_new_sentence_line(line):
    return line.startswith("\"*/Sentence")


def split_mlf(root_dir):
    """Splits the original MLF file into several files each describing single sentence."""
    with open(root_dir / ORIG_MLF, 'r', encoding='utf-8') as fr:
        fw = open(root_dir / MLF / "Sentence00001.mlf", 'w', encoding='utf-8')
        for line in fr:
            if is_new_sentence_line(line):
                fw.close()
                f_name = line[3:16] + ".mlf"
                fw = open(root_dir / MLF / f_name, 'w', encoding='utf-8')
            elif is_data_line(line):
                fw.write(line)
        fw.close()
